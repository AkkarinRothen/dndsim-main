"""
Combat Manager - Handles combat logic, character/monster loading, and combat configuration.

This module provides classes for managing D&D 5e combat simulations, including
party and enemy creation, combat configuration, and command handling.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from colors import Colors
from constants import CUSTOM_CHARS_DIR
from simulator_exceptions import CharacterLoadException, MonsterLoadException

if TYPE_CHECKING:
    from types import ModuleType


@dataclass
class CombatConfig:
    """
    Configuration for a combat encounter.
    
    Attributes:
        party_members: List of character keys/names to include in the party
        enemies: List of tuples containing (enemy_class, count)
        level: Character level for the party
        num_combats: Number of combat iterations to run (default: 1)
    """
    party_members: List[str]
    enemies: List[Tuple[type, int]]
    level: int
    num_combats: int = 1

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.party_members:
            raise ValueError("At least one party member is required")
        
        if not self.enemies:
            raise ValueError("At least one enemy is required")
        
        if not 1 <= self.level <= 20:
            raise ValueError(f"Level must be between 1 and 20, got {self.level}")
        
        if self.num_combats < 1:
            raise ValueError(f"num_combats must be at least 1, got {self.num_combats}")


class CombatManager:
    """
    Manages the creation and configuration of combat encounters.
    
    This class handles loading characters and monsters, creating combat instances,
    and managing combat state across multiple iterations.
    """
    
    def __init__(
        self,
        config: CombatConfig,
        configs_module: ModuleType,
        monster_configs_module: ModuleType,
        party_sim_module: ModuleType
    ):
        """
        Initialize the combat manager.
        
        Args:
            config: Combat configuration
            configs_module: Module containing character configurations
            monster_configs_module: Module containing monster configurations
            party_sim_module: Module containing party simulation logic
        """
        self.config = config
        self.configs = configs_module
        self.monster_configs = monster_configs_module
        self.party_sim = party_sim_module
    
    def create_party_instances(self) -> List[Any]:
        """
        Create character instances for the party.
        
        Returns:
            List of character instances
        
        Raises:
            CharacterLoadException: If any character cannot be loaded
        """
        party_instances = []
        
        for char_key in self.config.party_members:
            try:
                char_instance = self._load_character(char_key, self.config.level)
                party_instances.append(char_instance)
            except Exception as e:
                raise CharacterLoadException(
                    f"Failed to load character '{char_key}': {e}"
                ) from e
        
        if not party_instances:
            raise CharacterLoadException("No valid party members could be created")
        
        return party_instances
    
    def create_enemy_instances(self) -> List[Any]:
        """
        Create monster instances for the enemies.
        
        Returns:
            List of monster instances
        
        Raises:
            MonsterLoadException: If any monster cannot be created
        """
        enemy_instances = []
        
        for enemy_class, count in self.config.enemies:
            for j in range(count):
                try:
                    enemy_instance = enemy_class()
                    
                    # Add numbering for multiple enemies of the same type
                    if count > 1:
                        enemy_instance.name = f"{enemy_instance.name} {j + 1}"
                    
                    enemy_instances.append(enemy_instance)
                    
                except Exception as e:
                    raise MonsterLoadException(
                        f"Failed to create monster {enemy_class.__name__}: {e}"
                    ) from e
        
        if not enemy_instances:
            raise MonsterLoadException("No valid enemies could be created")
        
        return enemy_instances
    
    def create_combat(self, use_hooks: bool = True) -> Any:
        """
        Create a Combat instance with party and enemies.
        
        Args:
            use_hooks: Whether to attach resource tracker hooks to characters.
                      Should be False if the combat needs to be serialized.
        
        Returns:
            Combat instance ready for execution
        """
        from sim.resource_tracker import CombatResourceTracker, create_tracker_hooks

        party_instances = self.create_party_instances()
        enemy_instances = self.create_enemy_instances()

        # Initialize resource tracker
        combat_tracker = CombatResourceTracker()
        
        if use_hooks:
            for char_instance in party_instances:
                tracker = combat_tracker.add_character(char_instance)
                create_tracker_hooks(char_instance, tracker)
        
        return self.party_sim.Combat(
            party=party_instances,
            enemies=enemy_instances,
            combat_tracker=combat_tracker
        )
    
    def _load_character(self, char_key: str, level: int) -> Any:
        """
        Load a character from configs or custom character files.
        
        Args:
            char_key: Character identifier key
            level: Character level
        
        Returns:
            Character instance
        
        Raises:
            CharacterLoadException: If character cannot be loaded
        """
        # Try loading from built-in configs
        if char_key in self.configs.CONFIGS:
            try:
                return self.configs.CONFIGS[char_key].create(level)
            except Exception as e:
                raise CharacterLoadException(
                    f"Failed to create built-in character '{char_key}': {e}"
                ) from e
        
        # Try loading from custom characters
        custom_path = os.path.join(CUSTOM_CHARS_DIR, f"{char_key}.json")
        
        if os.path.exists(custom_path):
            return self._load_custom_character(custom_path, char_key, level)
        
        raise CharacterLoadException(
            f"Character '{char_key}' not found in configs or custom characters"
        )
    
    def _load_custom_character(
        self, 
        file_path: str, 
        char_key: str, 
        level: int
    ) -> Any:
        """
        Load a character from a custom JSON file.
        
        Args:
            file_path: Path to the JSON file
            char_key: Character key for error messages
            level: Character level
        
        Returns:
            Character instance
        
        Raises:
            CharacterLoadException: If the file cannot be parsed or character created
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
            
            # Validate required fields
            if 'class' not in char_data:
                raise CharacterLoadException(
                    f"Custom character '{char_key}' missing 'class' field"
                )
            
            # Get constructor from registry
            constructor = self.configs.CLASS_REGISTRY.get(char_data['class'])
            
            if not constructor:
                raise CharacterLoadException(
                    f"Unknown character class: {char_data['class']}"
                )
            
            # Create character with custom args
            args = char_data.get('args', {})
            return constructor(level=level, **args)
            
        except json.JSONDecodeError as e:
            raise CharacterLoadException(
                f"Invalid JSON in custom character '{char_key}': {e}"
            ) from e
        except (KeyError, TypeError) as e:
            raise CharacterLoadException(
                f"Invalid data format in custom character '{char_key}': {e}"
            ) from e
        except Exception as e:
            raise CharacterLoadException(
                f"Unexpected error loading custom character '{char_key}': {e}"
            ) from e


@dataclass
class CommandInfo:
    """Information about a combat command."""
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    handler: str = ""


class CombatCommands:
    """
    Manager for interactive combat commands.
    
    Provides a command system for interactive combat control, including
    inspecting combatants, advancing combat, and saving/loading state.
    """
    
    def __init__(self):
        """Initialize command registry."""
        self.commands: Dict[str, CommandInfo] = {
            'inspect': CommandInfo(
                aliases=['i', 'info'],
                description='Inspect a combatant (e.g., inspect Goblin 1)',
                handler='handle_inspect'
            ),
            'continue': CommandInfo(
                aliases=['c', 'next'],
                description='Advance to the next action',
                handler='handle_continue'
            ),
            'summary': CommandInfo(
                aliases=['s', 'stats'],
                description='Show combat summary',
                handler='handle_summary'
            ),
            'save': CommandInfo(
                aliases=[],
                description='Save combat state (e.g., save my_combat)',
                handler='handle_save'
            ),
            'load': CommandInfo(
                aliases=[],
                description='Load combat state (e.g., load my_combat)',
                handler='handle_load'
            ),
            'help': CommandInfo(
                aliases=['h', '?'],
                description='Show this help',
                handler='handle_help'
            ),
            'exit': CommandInfo(
                aliases=['quit', 'q'],
                description='Exit combat',
                handler='handle_exit'
            )
        }
    
    def show_help(self) -> None:
        """Display all available commands with descriptions."""
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}📖 AVAILABLE COMMANDS{Colors.ENDC}\n")
        
        for cmd_name, cmd_info in self.commands.items():
            aliases_str = ", ".join(cmd_info.aliases) if cmd_info.aliases else "no aliases"
            
            print(f"  {Colors.WARNING}{cmd_name:10s}{Colors.ENDC} ({aliases_str})")
            print(f"    {Colors.GRAY}{cmd_info.description}{Colors.ENDC}\n")
    
    def parse_command(self, input_str: str) -> Tuple[Optional[str], str]:
        """
        Parse user input into a command and its arguments.
        
        Args:
            input_str: Raw user input string
        
        Returns:
            Tuple of (command_name, arguments) or (None, "") if invalid
        """
        parts = input_str.strip().split(maxsplit=1)
        
        if not parts:
            return None, ""
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Search for command or alias
        for cmd_name, cmd_info in self.commands.items():
            if cmd == cmd_name or cmd in cmd_info.aliases:
                return cmd_name, args
        
        return None, ""
    
    def get_command_handler(self, command_name: str) -> Optional[str]:
        """
        Get the handler name for a command.
        
        Args:
            command_name: Name of the command
        
        Returns:
            Handler method name or None if command not found
        """
        cmd_info = self.commands.get(command_name)
        return cmd_info.handler if cmd_info else None
    
    def is_valid_command(self, command_name: str) -> bool:
        """
        Check if a command name is valid.
        
        Args:
            command_name: Command to check
        
        Returns:
            True if valid, False otherwise
        """
        return command_name in self.commands
    
    def get_all_command_names(self) -> List[str]:
        """
        Get a list of all command names.
        
        Returns:
            List of command names
        """
        return list(self.commands.keys())
    
    def get_all_aliases(self) -> Dict[str, str]:
        """
        Get a mapping of all aliases to their primary command names.
        
        Returns:
            Dictionary mapping aliases to command names
        """
        alias_map = {}
        for cmd_name, cmd_info in self.commands.items():
            for alias in cmd_info.aliases:
                alias_map[alias] = cmd_name
        return alias_map


def validate_combat_participants(
    party_members: List[str],
    enemies: List[Tuple[type, int]]
) -> Tuple[bool, Optional[str]]:
    """
    Validate combat participant configuration.
    
    Args:
        party_members: List of party member identifiers
        enemies: List of (enemy_class, count) tuples
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not party_members:
        return False, "Party cannot be empty"
    
    if not enemies:
        return False, "At least one enemy is required"
    
    total_enemies = sum(count for _, count in enemies)
    if total_enemies == 0:
        return False, "Total enemy count must be greater than 0"
    
    if total_enemies > 50:
        return False, f"Too many enemies ({total_enemies}), maximum is 50"
    
    if len(party_members) > 10:
        return False, f"Too many party members ({len(party_members)}), maximum is 10"
    
    return True, None


def create_combat_summary(combat: Any) -> Dict[str, Any]:
    """
    Create a summary dictionary of combat results.
    
    Args:
        combat: Combat instance
    
    Returns:
        Dictionary with combat statistics
    """
    return {
        'rounds': combat.rounds,
        'winner': combat._determine_winner() if combat.is_over() else None,
        'party_survivors': sum(
            1 for c in combat.combatants 
            if c.team == 'party' and not c.is_down
        ),
        'enemy_survivors': sum(
            1 for c in combat.combatants 
            if c.team == 'enemies' and not c.is_down
        ),
        'total_damage_dealt': getattr(combat, 'total_damage', 0),
        'is_over': combat.is_over()
    }