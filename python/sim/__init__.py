"""
Core simulation engine for D&D 5e DPR (Damage Per Round) calculations.

This module provides the main simulation framework for testing character builds
against various targets and monsters. It handles:
- Single character DPR testing
- Multi-character comparison
- Monster-specific combat simulation
- Parallel processing for performance
"""

from typing import Callable, Any, Union, Literal, Tuple, List, Optional, TYPE_CHECKING
import random
import multiprocessing.pool

if TYPE_CHECKING:
    import sim.character
    import sim.target

from sim.monster import BaseMonster
from .character_config import CharacterConfig
from util.log import log


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

# Ability score types for D&D 5e
Stat = Literal["str", "dex", "con", "int", "wis", "cha", "none"]

# Valid target types for simulation
TargetType = Union["sim.target.Target", BaseMonster]


# ============================================================================
# CONSTANTS
# ============================================================================

# Default monster name for generic AC/HP scaling target
DEFAULT_MONSTER = "generic"
GENERIC_TARGET_ALIASES = {"generic", "target"}

# Maximum iterations to prevent performance issues
MAX_ITERATIONS = 10000

# Combat round limits
DEFAULT_ROUNDS_PER_FIGHT = 5
DEFAULT_FIGHTS_PER_REST = 3
DEFAULT_ITERATIONS = 500


# ============================================================================
# SIMULATION CLASSES
# ============================================================================

class Simulation:
    """
    A single simulation run for testing character DPR.
    
    Simulates multiple fights, each consisting of multiple rounds,
    with short rests between fights. Tracks total damage dealt to
    the target across all fights and rounds.
    
    Attributes:
        character: The character being tested
        target: The target/monster being attacked
        num_fights: Number of fights before long rest
        num_rounds: Number of rounds per fight
    """
    
    def __init__(
        self,
        character: "sim.character.Character",
        target: TargetType,
        num_fights: int,
        num_rounds: int,
    ) -> None:
        """
        Initialize a simulation.
        
        Args:
            character: Character to test
            target: Target or monster to attack
            num_fights: Number of fights to simulate
            num_rounds: Rounds per fight
            
        Raises:
            ValueError: If num_fights or num_rounds are not positive
        """
        if num_fights < 1:
            raise ValueError(f"num_fights must be positive, got {num_fights}")
        if num_rounds < 1:
            raise ValueError(f"num_rounds must be positive, got {num_rounds}")
        
        self.character = character
        self.target = target
        self.num_fights = num_fights
        self.num_rounds = num_rounds

    def run(self) -> None:
        """
        Execute the simulation.
        
        Process:
        1. Start with long rest (full resources)
        2. Run specified number of fights
        3. Each fight has specified number of rounds
        4. Short rest between fights
        5. Log damage sources at the end
        """
        # Both character and target start at full strength
        self.character.long_rest()
        self.target.long_rest()
        
        # Simulate multiple fights
        for fight_num in range(self.num_fights):
            # Each fight consists of multiple rounds
            for round_num in range(self.num_rounds):
                # Character's turn
                self.character.turn(self.target, round_number=round_num)
                
                # Enemy's turn (may trigger reactions like Retaliation)
                self.character.enemy_turn(self.target)
                
                # Target's turn (for monsters with active abilities)
                self.target.turn()
            
            # Short rest between fights (restore some resources)
            # Don't rest after the last fight
            if fight_num < self.num_fights - 1:
                self.character.short_rest()
        
        # Log detailed damage breakdown
        self.target.log_damage_sources()

    def get_total_damage(self) -> float:
        """
        Get total damage dealt in this simulation.
        
        Returns:
            Total damage dealt to target
        """
        return self.target.dmg

    def get_dpr(self) -> float:
        """
        Calculate damage per round for this simulation.
        
        Returns:
            Average damage per round
        """
        total_rounds = self.num_fights * self.num_rounds
        return self.target.dmg / total_rounds if total_rounds > 0 else 0.0


class Args:
    """
    Arguments container for parallel character testing.
    
    Encapsulates all parameters needed to test a character build
    across multiple levels. Used for multiprocessing distribution.
    """
    
    def __init__(
        self,
        character: str,
        start_level: int,
        end_level: int,
        iterations: int,
        num_rounds: int,
        num_fights: int,
        debug: bool,
        monster_name: str,
    ) -> None:
        """
        Initialize test arguments.
        
        Args:
            character: Character configuration key
            start_level: Starting level for testing
            end_level: Ending level for testing
            iterations: Number of simulation runs per level
            num_rounds: Rounds per fight
            num_fights: Fights per simulation
            debug: Whether to enable debug logging
            monster_name: Monster to test against
            
        Raises:
            ValueError: If levels or iterations are invalid
        """
        if not 1 <= start_level <= 20:
            raise ValueError(f"start_level must be 1-20, got {start_level}")
        if not 1 <= end_level <= 20:
            raise ValueError(f"end_level must be 1-20, got {end_level}")
        if start_level > end_level:
            raise ValueError(
                f"start_level ({start_level}) cannot exceed end_level ({end_level})"
            )
        if iterations < 1:
            raise ValueError(f"iterations must be positive, got {iterations}")
        if iterations > MAX_ITERATIONS:
            raise ValueError(
                f"iterations ({iterations}) exceeds maximum ({MAX_ITERATIONS})"
            )
        
        self.character = character
        self.start_level = start_level
        self.end_level = end_level
        self.iterations = iterations
        self.num_rounds = num_rounds
        self.num_fights = num_fights
        self.debug = debug
        self.monster_name = monster_name


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_levels(levels: str) -> Tuple[int, int]:
    """
    Parse level range string into start and end levels.
    
    Args:
        levels: Level specification as string
               - Single level: "5" -> (5, 5)
               - Range: "1-20" -> (1, 20)
    
    Returns:
        Tuple of (start_level, end_level)
        
    Raises:
        ValueError: If format is invalid or levels out of range
        
    Examples:
        >>> parse_levels("5")
        (5, 5)
        >>> parse_levels("1-20")
        (1, 20)
        >>> parse_levels("10-15")
        (10, 15)
    """
    try:
        if "-" in levels:
            start, end = levels.split("-")
            start_level = int(start)
            end_level = int(end)
        else:
            start_level = end_level = int(levels)
        
        # Validate range
        if not 1 <= start_level <= 20:
            raise ValueError(f"Start level must be 1-20, got {start_level}")
        if not 1 <= end_level <= 20:
            raise ValueError(f"End level must be 1-20, got {end_level}")
        if start_level > end_level:
            raise ValueError(
                f"Start level ({start_level}) cannot exceed end level ({end_level})"
            )
        
        return start_level, end_level
    
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Invalid level format: '{levels}'. Use '5' or '1-20'")
        raise


def create_target(monster_name: str, level: int) -> TargetType:
    """
    Create appropriate target based on monster name.
    
    Args:
        monster_name: Name of the monster or 'generic'
        level: Character level (for generic target scaling)
    
    Returns:
        Target instance (generic or specific monster)
        
    Raises:
        ValueError: If monster name is unknown
    """
    import sim.target
    
    # Generic target with level-appropriate AC/HP
    if monster_name.lower() in GENERIC_TARGET_ALIASES:
        return sim.target.Target(level)
    
    # Specific monster from monster_configs
    try:
        import monster_configs
        monster_class = monster_configs.get_monster_class(monster_name)
        if monster_class:
            return monster_class()
    except (ImportError, AttributeError):
        pass
    
    # Unknown monster
    raise ValueError(
        f"Unknown monster: '{monster_name}'. "
        f"Use 'generic' or a valid monster name from monster_configs."
    )


# ============================================================================
# CORE TESTING FUNCTIONS
# ============================================================================

def test_dpr(
    character: "sim.character.Character",
    level: int,
    num_fights: int,
    num_rounds: int,
    iterations: int,
    monster_name: str,
) -> float:
    """
    Calculate average Damage Per Round (DPR) for a character.
    
    Runs multiple iterations of combat simulation and averages
    the damage dealt per round across all iterations.
    
    Args:
        character: Character instance to test
        level: Character level
        num_fights: Fights per simulation
        num_rounds: Rounds per fight
        iterations: Number of simulation runs
        monster_name: Target monster name
    
    Returns:
        Average damage per round
        
    Formula:
        DPR = Total Damage / (num_fights * num_rounds * iterations)
        
    Raises:
        ValueError: If parameters are invalid
    """
    if iterations < 1:
        raise ValueError(f"iterations must be positive, got {iterations}")
    
    total_damage = 0.0
    
    for _ in range(iterations):
        # Create fresh target for each iteration
        target = create_target(monster_name, level)
        
        # Run simulation
        simulation = Simulation(character, target, num_fights, num_rounds)
        simulation.run()
        
        # Accumulate damage
        total_damage += simulation.get_total_damage()
    
    # Calculate average DPR
    total_rounds = num_fights * num_rounds * iterations
    return total_damage / total_rounds if total_rounds > 0 else 0.0


def test_character(args: Args) -> List[List[Any]]:
    """
    Test a character across a level range.
    
    This is the worker function for parallel processing.
    Tests one character configuration across all specified levels.
    
    Args:
        args: Test arguments container
    
    Returns:
        List of [level, character_name, dpr, log_data] for each level
        
    Side Effects:
        - May enable logging if args.debug is True
        - Prints debug report if args.debug is True
    """
    import sim.character
    
    # Enable debug logging if requested
    if args.debug:
        log.enable()
    
    # Get character configuration
    try:
        import configs
        config = configs.get_configs([args.character])[0]
    except (ImportError, IndexError, KeyError) as e:
        raise ValueError(
            f"Could not load character configuration '{args.character}': {e}"
        )
    
    data = []
    
    # Test each level in the range
    for level in range(args.start_level, args.end_level + 1):
        # Clear previous logs
        log.record_.clear()
        
        # Calculate DPR for this level
        dpr = test_dpr(
            character=config.create(level),
            level=level,
            num_rounds=args.num_rounds,
            num_fights=args.num_fights,
            iterations=args.iterations,
            monster_name=args.monster_name,
        )
        
        # Store results with log data
        data.append([level, config.name, dpr, log.record_.copy()])
    
    # Print debug report if enabled
    if args.debug:
        log.printReport()
    
    return data


def test_characters(
    characters: List[str],
    start_level: int,
    end_level: int,
    num_rounds: int = DEFAULT_ROUNDS_PER_FIGHT,
    num_fights: int = DEFAULT_FIGHTS_PER_REST,
    iterations: int = DEFAULT_ITERATIONS,
    debug: bool = False,
    monster_name: str = DEFAULT_MONSTER,
) -> List[List[Any]]:
    """
    Test multiple characters in parallel across a level range.
    
    This is the main entry point for DPR testing. Uses multiprocessing
    to test characters in parallel for better performance.
    
    Args:
        characters: List of character configuration keys
        start_level: Starting level for testing (1-20)
        end_level: Ending level for testing (1-20)
        num_rounds: Rounds per fight (default: 5)
        num_fights: Fights per simulation (default: 3)
        iterations: Simulation runs per level (default: 500)
        debug: Enable debug logging (default: False)
        monster_name: Target monster name (default: 'generic')
    
    Returns:
        List of results in format:
        [["Level", "Character", "DPR", "Log"],
         [level, name, dpr, log_data],
         ...]
        
    Raises:
        ValueError: If parameters are invalid
        
    Performance:
        Uses multiprocessing.Pool for parallel execution.
        Each character is tested in a separate process.
        
    Example:
        >>> results = test_characters(
        ...     characters=["fighter", "barbarian"],
        ...     start_level=1,
        ...     end_level=20,
        ...     num_rounds=5,
        ...     num_fights=3,
        ...     iterations=500,
        ...     debug=False,
        ...     monster_name="generic"
        ... )
        >>> # results[0] is header row
        >>> # results[1:] are data rows
    """
    if not characters:
        raise ValueError("Must provide at least one character to test")
    
    # Initialize with header row
    data = [["Level", "Character", "DPR", "Log"]]
    
    # Create argument sets for each character
    args_list = [
        Args(
            character=character,
            start_level=start_level,
            end_level=end_level,
            iterations=iterations,
            num_rounds=num_rounds,
            num_fights=num_fights,
            debug=debug,
            monster_name=monster_name,
        )
        for character in characters
    ]
    
    # Run tests in parallel using multiprocessing
    with multiprocessing.pool.Pool() as pool:
        outputs = pool.map(test_character, args_list)
        
        # Aggregate results
        for output in outputs:
            data.extend(output)
    
    return data


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Classes
    "Simulation",
    "Args",
    
    # Type definitions
    "Stat",
    "TargetType",
    
    # Utility functions
    "parse_levels",
    "create_target",
    
    # Testing functions
    "test_dpr",
    "test_character",
    "test_characters",
    
    # Constants
    "DEFAULT_MONSTER",
    "DEFAULT_ROUNDS_PER_FIGHT",
    "DEFAULT_FIGHTS_PER_REST",
    "DEFAULT_ITERATIONS",
    "MAX_ITERATIONS",
]
