"""
Party vs Monster combat simulation engine for D&D 5e.

This module provides a full combat simulation system that handles:
- Initiative tracking
- Turn-based combat
- HP tracking and defeat detection
- Multi-combatant encounters
- Combat outcome statistics

Unlike the single-character DPR simulator, this engine simulates
realistic combat with turn order, targeting, and win/loss conditions.
"""

import random
from typing import List, Dict, Any, Union, Literal, Optional
from dataclasses import dataclass

from sim.resource_tracker import CombatResourceTracker, create_tracker_hooks

# We can't import Character or BaseMonster directly due to circular imports
# Type hints use strings for forward references
EntityType = Any  # Union[Character, BaseMonster] in practice


# ============================================================================
# CONSTANTS
# ============================================================================

# Combat parameters
MAX_COMBAT_ROUNDS = 100  # Prevent infinite combat loops
DEFAULT_ITERATIONS = 100  # Default number of combat simulations

# Combat outcomes
PARTY_WIN = "party"
MONSTER_WIN = "monsters"
DRAW = "nobody"

# Combatant states
STATUS_ALIVE = "alive"
STATUS_DEFEATED = "defeated"

# Team identifiers
TEAM_PARTY = "party"
TEAM_ENEMIES = "enemies"


# ============================================================================
# COMBAT STATE TRACKING
# ============================================================================

class Combatant:
    """
    Wrapper for a character or monster to track combat-specific state.
    
    Maintains separate combat state (current HP, initiative, defeated status)
    from the underlying entity's permanent state. This allows the same
    entity to be used in multiple combats.
    
    Attributes:
        entity: The underlying character or monster
        name: Display name for combat logs
        team: Which side this combatant is on ('party' or 'enemies')
        initiative: Initiative roll result
        current_hp: Current hit points in this combat
        is_down: Whether the combatant has been defeated
    """
    
    def __init__(self, entity: EntityType, team: str):
        """
        Initialize a combatant wrapper.
        
        Args:
            entity: Character or monster instance
            team: Team identifier ('party' or 'enemies')
            
        Note:
            To avoid circular imports, entity is not type-hinted.
            In practice, it's Union[Character, BaseMonster].
        """
        self.entity = entity
        self.name: str = entity.name
        self.team: str = team
        self.initiative: int = 0
        self.current_hp: int = entity.hp
        self.is_down: bool = False

    def roll_initiative(self) -> None:
        """
        Roll initiative for this combatant.
        
        Uses d20 + Dexterity modifier, following D&D 5e rules.
        Higher initiative acts earlier in the round.
        """
        dex_modifier = self.entity.mod('dex')
        self.initiative = random.randint(1, 20) + dex_modifier

    def is_alive(self) -> bool:
        """
        Check if this combatant is still in the fight.
        
        Returns:
            True if not defeated, False otherwise
        """
        return not self.is_down

    def take_damage(self) -> None:
        """
        Sync HP from entity and check for defeat.
        
        Updates current_hp from the entity's HP (which changes during
        their turn) and marks the combatant as down if HP <= 0.
        """
        self.current_hp = self.entity.hp
        if self.current_hp <= 0 and not self.is_down:
            self.is_down = True
            self.current_hp = 0

    def copy(self):
        """Returns a copy of the combatant."""
        import copy
        return copy.deepcopy(self)


# ============================================================================
# COMBAT ENGINE
# ============================================================================

class Combat:
    """
    Main engine for running a single combat encounter.
    
    Handles all aspects of combat simulation:
    - Initiative rolling and turn order
    - Round-by-round execution
    - Target selection
    - Victory condition checking
    - Combat state tracking
    
    The combat continues until one side is eliminated or the
    maximum round limit is reached.
    """
    
    def __init__(self, party: List[EntityType], enemies: List[EntityType], combat_tracker=None):
        """
        Initialize a combat encounter.
        
        Args:
            party: List of party member entities
            enemies: List of enemy monster entities
            combat_tracker: Optional resource tracker
        """
        # Wrap entities in combat state trackers
        self.party: List[Combatant] = [
            Combatant(c, TEAM_PARTY) for c in party
        ]
        self.enemies: List[Combatant] = [
            Combatant(e, TEAM_ENEMIES) for e in enemies
        ]
        
        # Combined list for iteration
        self.combatants: List[Combatant] = self.party + self.enemies
        
        # Combat tracking
        self.turn_order: List[Combatant] = []
        self.combat_log: List[str] = []
        self.rounds: int = 0
        self.combat_tracker = combat_tracker

    def setup_combat(self) -> None:
        """
        Prepare for combat by rolling initiative and setting turn order.
        
        Process:
        1. Each combatant takes a long rest (full HP, full resources)
        2. Roll initiative for each combatant
        3. Sort combatants by initiative (highest first)
        4. Log the turn order
        """
        # Reset all combatants to full strength
        for combatant in self.combatants:
            combatant.entity.long_rest()
            combatant.roll_initiative()
        
        # Determine turn order (highest initiative first)
        self.turn_order = sorted(
            self.combatants,
            key=lambda c: c.initiative,
            reverse=True
        )
        
        # Log combat start
        turn_order_names = ", ".join(c.name for c in self.turn_order)
        self.log(f"Combat starts! Turn order: {turn_order_names}")

    def run_combat(self) -> Dict[str, Any]:
        """
        Execute the entire combat from start to finish.
        
        Returns:
            Combat result dictionary containing:
            - winner: 'party', 'monsters', or 'nobody'
            - rounds: Number of rounds fought
            - final_state: List of combatant final states
            
        Process:
        1. Setup combat (initiative, etc.)
        2. Run rounds until victory or round limit
        3. Each round, each combatant takes their turn
        4. Check for victory after each round
        5. Return combat results
        """
        self.setup_combat()
        
        while not self.is_over():
            self.run_combat_turn()
        
        # Determine winner
        winner = self._determine_winner()
        
        return {
            "winner": winner,
            "rounds": self.rounds,
            "final_state": self.get_final_state()
        }

    def _get_valid_targets(self, combatant: Combatant) -> List[Combatant]:
        """
        Get list of valid targets for a combatant.
        
        Args:
            combatant: The combatant selecting a target
            
        Returns:
            List of alive combatants on the opposing team
        """
        if combatant.team == TEAM_PARTY:
            # Party members target enemies
            return [e for e in self.enemies if e.is_alive()]
        else:
            # Enemies target party members
            return [p for p in self.party if p.is_alive()]

    def _get_injured_allies(self, combatant: Combatant) -> List[Combatant]:
        """
        Get list of injured allies for a combatant.
        
        Args:
            combatant: The combatant whose allies to check.
            
        Returns:
            List of alive but injured combatants on the same team.
        """
        allies = self.party if combatant.team == TEAM_PARTY else self.enemies
        return [ally for ally in allies if ally.is_alive() and ally.current_hp < ally.entity.max_hp]

    def _select_target_simple(self, combatant: Combatant, targets: List[Combatant]) -> Combatant:
        """AI: Target the combatant with the lowest current HP."""
        lowest_hp_target = min(targets, key=lambda t: t.current_hp)
        
        # If all targets are at full HP, choose randomly
        if all(t.current_hp == t.entity.max_hp for t in targets):
            return random.choice(targets)
            
        return lowest_hp_target

    def _select_target_brute(self, combatant: Combatant, targets: List[Combatant]) -> Combatant:
        """AI: Target the combatant with the highest threat_rating."""
        highest_threat_target = max(targets, key=lambda t: t.entity.threat_rating)
        return highest_threat_target

    def _select_target(self, combatant: Combatant, targets: List[Combatant]) -> Combatant:
        """
        Selects a target for a combatant based on its AI behavior.
        
        Args:
            combatant: The combatant selecting a target
            targets: List of valid targets
            
        Returns:
            The selected target
        """
        ai_behavior = combatant.entity.ai_behavior
        
        if ai_behavior == 'brute':
            target = self._select_target_brute(combatant, targets)
            self.log(f"{combatant.name} (AI: Brute) targets {target.name} (Threat: {target.entity.threat_rating})")
            return target
        
        if ai_behavior == 'caster':
            # For now, casters will use simple logic. This can be expanded.
            target = self._select_target_simple(combatant, targets)
            self.log(f"{combatant.name} (AI: Caster) targets {target.name} (HP: {target.current_hp})")
            return target
        
        # Default to simple AI
        target = self._select_target_simple(combatant, targets)
        self.log(f"{combatant.name} (AI: Simple) targets {target.name} (HP: {target.current_hp})")
        return target

    def run_combat_turn(self):
        """Runs a single turn of combat."""
        if self.is_over():
            return
            
        if not self.turn_order:
            self.setup_combat()

        combatant = self.turn_order[0]
        self.turn_order = self.turn_order[1:] + [self.turn_order[0]]

        if combatant.is_down:
            return

        targets = self._get_valid_targets(combatant)
        if not targets:
            return

        # Use AI for enemies, simple selection for party members
        if combatant.team == TEAM_ENEMIES:
            target = self._select_target(combatant, targets)
        else:
            # Party members' logic is in their 'turn' method,
            # but we still need to provide a default target.
            target = targets[0]
            
        combatant.entity.turn(target.entity, round_number=self.rounds, combat=self)
        target.take_damage()
        
        if len(self.turn_order) > 0 and self.turn_order[0] == self.combatants[0]:
            self.rounds += 1
            
    def recreate_turn_order(self) -> None:
        """
        Re-establishes the turn order by re-rolling initiative for all combatants.
        
        This method is used when deserialization fails to restore the exact
        previous turn order, allowing combat to continue without resetting
        combatants' HP or other states.
        """
        for combatant in self.combatants:
            combatant.roll_initiative()
        
        self.turn_order = sorted(
            self.combatants,
            key=lambda c: c.initiative,
            reverse=True
        )
        self.log("Turn order re-established after deserialization.")
            
    def is_over(self) -> bool:
        """Checks if the combat is over."""
        party_alive = any(c.is_alive() for c in self.party)
        enemies_alive = any(e.is_alive() for e in self.enemies)
        return not party_alive or not enemies_alive or self.rounds >= MAX_COMBAT_ROUNDS

    def party_wins(self) -> bool:
        """Checks if the party has won."""
        return any(c.is_alive() for c in self.party) and not any(e.is_alive() for e in self.enemies)
        
    def monsters_win(self) -> bool:
        """Checks if the monsters have won."""
        return not any(c.is_alive() for c in self.party) and any(e.is_alive() for e in self.enemies)

    def _determine_winner(self) -> str:
        """
        Determine the combat outcome.
        
        Returns:
            Winner identifier: 'party', 'monsters', or 'nobody'
        """
        if self.party_wins():
            return PARTY_WIN
        elif self.monsters_win():
            return MONSTER_WIN
        else:
            return DRAW  # Should rarely happen

    def get_final_state(self) -> List[Dict[str, str]]:
        """
        Get a summary of all combatants' final states.
        
        Returns:
            List of dictionaries containing:
            - name: Combatant name
            - team: Team identifier
            - status: 'alive' or 'defeated'
            - hp: HP string in format "current/max"
            
        Example:
            [
                {
                    "name": "Fighter",
                    "team": "party",
                    "status": "alive",
                    "hp": "45/60"
                },
                ...
            ]
        """
        state = []
        for combatant in self.combatants:
            status = STATUS_DEFEATED if combatant.is_down else STATUS_ALIVE
            state.append({
                "name": combatant.name,
                "team": combatant.team,
                "status": status,
                "hp": f"{combatant.current_hp}/{combatant.entity.max_hp}"
            })
        return state

    def get_combatant(self, entity: EntityType) -> Optional[Combatant]:
        """Finds the Combatant wrapper for a given entity."""
        for combatant in self.combatants:
            if combatant.entity is entity:
                return combatant
        return None

    def log(self, message: str) -> None:
        """
        Log a combat message.
        
        Args:
            message: Message to log
            
        Note:
            Logging is currently disabled for performance.
            Can be re-enabled for debugging by uncommenting
            the combat_log append statement.
        """
        # Logging disabled for performance
        # Uncomment for debugging:
        self.combat_log.append(message)
        pass

    def copy(self):
        """Returns a copy of the combat."""
        import copy
        return copy.deepcopy(self)


# ============================================================================
# TESTING AND STATISTICS
# ============================================================================

@dataclass
class CombatStatistics:
    """
    Aggregated statistics from multiple combat simulations.
    
    Attributes:
        party_win_rate: Percentage of combats won by the party
        avg_rounds: Average number of rounds per combat
        last_combat_report: Detailed results from the last combat
    """
    party_win_rate: float
    avg_rounds: float
    last_combat_report: Dict[str, Any]


def test_party_combat(
    party_configs: List[Any],  # List[CharacterConfig]
    enemy_configs_and_counts: List[tuple],  # List[Tuple[MonsterClass, int]]
    level: int,
    iterations: int = DEFAULT_ITERATIONS
) -> Dict[str, Any]:
    """
    Run multiple iterations of party combat and aggregate results.
    
    This is the main entry point for party combat simulation.
    Runs the specified number of combat iterations and calculates
    win rate and average combat duration statistics.
    
    Args:
        party_configs: List of CharacterConfig objects for party members
        enemy_configs_and_counts: List of (MonsterClass, count) tuples
        level: Party level (for character creation)
        iterations: Number of combat simulations to run
        
    Returns:
        Dictionary containing:
        - party_win_rate: Percentage of party victories
        - avg_rounds: Average combat duration in rounds
        - last_combat_report: Full report from final combat
        
    Example:
        >>> from sim.character_config import CharacterConfig
        >>> party_configs = [
        ...     CharacterConfig(name="Fighter", constructor=Fighter),
        ...     CharacterConfig(name="Wizard", constructor=Wizard),
        ... ]
        >>> enemy_configs = [(Goblin, 4), (Hobgoblin, 1)]
        >>> results = test_party_combat(party_configs, enemy_configs, level=3)
        >>> print(f"Party wins {results['party_win_rate']:.1f}% of the time")
        
    Performance:
        Each iteration creates fresh instances of all combatants
        to ensure independent results. Runtime scales linearly
        with iterations.
    """
    # Statistics tracking
    party_wins = 0
    total_rounds = 0
    last_combat_report = {}

    for i in range(iterations):
        # Create fresh party for this iteration
        party = []
        for config in party_configs:
            char_instance = config.create(level)
            char_instance.name = config.name
            party.append(char_instance)
        
        # Initialize resource tracker for this combat iteration
        combat_tracker = CombatResourceTracker()
        for char_instance in party:
            tracker = combat_tracker.add_character(char_instance)
            create_tracker_hooks(char_instance, tracker)

        # Create fresh enemies for this iteration
        enemies = []
        for enemy_class, count in enemy_configs_and_counts:
            for j in range(count):
                enemy_instance = enemy_class()
                # Add numbering for multiple enemies of same type
                if count > 1:
                    enemy_instance.name = f"{enemy_instance.name} {j+1}"
                enemies.append(enemy_instance)

        # Run combat
        combat = Combat(party, enemies)
        while not combat.is_over():
            combat.run_combat_turn()
        
        result = {
            "winner": combat._determine_winner(),
            "rounds": combat.rounds,
            "final_state": combat.get_final_state()
        }

        # Update statistics
        if result['winner'] == PARTY_WIN:
            party_wins += 1
        total_rounds += result['rounds']
        
        # Save last combat for detailed reporting
        if i == iterations - 1:
            last_combat_report = result
            last_combat_report['combat_tracker'] = combat_tracker

    # Calculate aggregated statistics
    win_rate = (party_wins / iterations) * 100 if iterations > 0 else 0
    avg_rounds = total_rounds / iterations if iterations > 0 else 0

    # Print resource usage summary for the last combat iteration
    if iterations > 0 and 'combat_tracker' in last_combat_report:
        print("\n" + "="*80)
        print("          RESUMEN DE USO DE RECURSOS DEL ÚLTIMO COMBATE")
        print("="*80)
        last_combat_report['combat_tracker'].print_all_summaries()

    final_results = {
        "party_win_rate": win_rate,
        "avg_rounds": avg_rounds,
        "last_combat_report": last_combat_report
    }
    # Remove tracker before returning to avoid issues with serialization if any
    if 'combat_tracker' in final_results['last_combat_report']:
        del final_results['last_combat_report']['combat_tracker']

    return final_results


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    "Combatant",
    "Combat",
    "CombatStatistics",
    "test_party_combat",
    "PARTY_WIN",
    "MONSTER_WIN",
    "DRAW",
    "STATUS_ALIVE",
    "STATUS_DEFEATED",
]
