import random
from typing import Dict, List, Optional
from collections import defaultdict

from util.taggable import Taggable
from util.util import do_roll
from sim.spells import Spellcasting, Spellcaster
from sim.event_loop import EventLoop


class BaseMonster(Taggable):
    """
    Base class for all monsters and creatures.
    
    Provides common attributes like AC, HP, ability scores, and damage
    resistances/vulnerabilities/immunities. Can perform basic attacks
    and saving throws.
    
    Attributes:
        name: Monster's display name
        ac: Armor Class
        hp: Current hit points
        max_hp: Maximum hit points
        stats: Dictionary of ability scores
        prof_bonus: Proficiency bonus
        resistances: List of damage types monster resists (half damage)
        vulnerabilities: List of damage types monster is vulnerable to (double damage)
        immunities: List of damage types monster is immune to (no damage)
        dmg: Total damage taken
        stunned: Whether monster is stunned
        prone: Whether monster is prone
        grappled: Whether monster is grappled
    """
    
    def __init__(
        self,
        name: str,
        ac: int,
        hp: int,
        str_score: int,
        dex: int,
        con: int,
        int_score: int,
        wis: int,
        cha: int,
        prof_bonus: int,
        resistances: Optional[List[str]] = None,
        vulnerabilities: Optional[List[str]] = None,
        immunities: Optional[List[str]] = None,
        ai_behavior: str = 'simple',
        spellcasting_ability: Optional[str] = None,
        spells: Optional[List[any]] = None,
        caster_level: int = 1,
    ):
        """
        Initialize a monster.
        
        Args:
            name: Monster's name
            ac: Armor Class
            hp: Hit points
            str_score: Strength score
            dex: Dexterity score
            con: Constitution score
            int_score: Intelligence score
            wis: Wisdom score
            cha: Charisma score
            prof_bonus: Proficiency bonus
            resistances: Damage types resisted
            vulnerabilities: Damage types vulnerable to
            immunities: Damage types immune to
            ai_behavior: AI behavior profile ('simple', 'brute', etc.)
            spellcasting_ability: Spellcasting ability ('int', 'wis', 'cha')
            spells: List of spell objects known by the monster
            caster_level: The monster's caster level for spell slot purposes
        """
        super().__init__()
        
        self.name = name
        self.ac = ac
        self.max_hp = hp
        self.hp = hp
        self.events = EventLoop()
        
        # Ability scores
        self.stats: Dict[str, int] = {
            'str': str_score,
            'dex': dex,
            'con': con,
            'int': int_score,
            'wis': wis,
            'cha': cha
        }
        
        self.prof_bonus = prof_bonus
        self.ai_behavior = ai_behavior
        self.level = caster_level # For spellcasting purposes
        
        # Damage modifiers
        self.resistances = resistances if resistances is not None else []
        self.vulnerabilities = vulnerabilities if vulnerabilities is not None else []
        self.immunities = immunities if immunities is not None else []
        
        # Spellcasting
        self.spells = None
        if spellcasting_ability:
            # Monsters are treated as 'Full' casters for slot calculation based on their caster_level
            self.spells = Spellcasting(self, spellcasting_ability, [(Spellcaster.FULL, caster_level)])
            if spells:
                for spell in spells:
                    self.spells.add_spell(spell)

        # Initialize combat state
        self.long_rest()

    def mod(self, ability: str) -> int:
        """
        Calculate ability modifier from score.
        
        Args:
            ability: Ability name ('str', 'dex', etc.)
            
        Returns:
            Ability modifier
            
        Raises:
            KeyError: If ability name is invalid
        """
        if ability not in self.stats:
            raise KeyError(f"Invalid ability: {ability}")
        
        return (self.stats[ability] - 10) // 2

    def get_save_bonus(self, ability: str) -> int:
        """
        Get saving throw bonus for an ability.
        
        Currently assumes proficiency in all saves. Override in subclasses
        to implement specific save proficiencies.
        
        Args:
            ability: Ability to save with
            
        Returns:
            Save bonus (ability mod + proficiency)
        """
        return self.mod(ability) + self.prof_bonus

    def long_rest(self) -> None:
        """
        Take a long rest, fully recovering HP and clearing conditions.
        """
        self.hp = self.max_hp
        self.dmg = 0
        self.poisoned = False
        self._dmg_log: Dict[str, int] = defaultdict(int)
        if self.spells:
            self.spells.long_rest()
        self.short_rest()

    def short_rest(self) -> None:
        """
        Take a short rest, clearing temporary conditions.
        """
        self.stunned = False
        self.stun_turns = 0
        self.grappled = False
        self.prone = False
        self.semistunned = False
        self.poisoned = False

    def apply_damage(self, damage: int, damage_type: str, source: str) -> None:
        """
        Apply damage to monster with resistances/vulnerabilities/immunities.
        
        Damage is modified based on:
        - Immunity: No damage taken
        - Resistance: Half damage (rounded down)
        - Vulnerability: Double damage
        
        Args:
            damage: Base damage amount
            damage_type: Type of damage (e.g., 'fire', 'slashing')
            source: Source of damage (for logging)
            
        Note:
            This uses simple substring matching for damage types.
            More complex conditions (e.g., "from nonmagical attacks") are
            not fully supported.
        """
        # Normalize damage type for case-insensitive matching
        damage_type_lower = damage_type.lower()
        
        # Check immunity first (no damage)
        is_immune = any(
            damage_type_lower in immunity.lower()
            for immunity in self.immunities
        )
        
        if is_immune:
            damage = 0
        else:
            # Check resistance (half damage)
            is_resistant = any(
                damage_type_lower in resistance.lower()
                for resistance in self.resistances
            )
            
            # Check vulnerability (double damage)
            is_vulnerable = any(
                damage_type_lower in vulnerability.lower()
                for vulnerability in self.vulnerabilities
            )
            
            if is_resistant:
                damage //= 2
            elif is_vulnerable:
                damage *= 2
        
        # Apply final damage
        self.hp -= damage
        self.dmg += damage
        self._dmg_log[source] += damage

    def log_damage_sources(self) -> None:
        """
        Log all damage sources and total damage to combat log.
        """
        for source, damage in self._dmg_log.items():
            # This uses the global log, which is not ideal for testing
            pass
        # log.record("Damage (Total)", self.dmg)

    def save(self, ability: str, dc: int) -> bool:
        """
        Make a saving throw.
        
        Args:
            ability: Ability to save with ('str', 'dex', etc.)
            dc: Difficulty Class to beat
            
        Returns:
            True if save succeeded, False otherwise
        """
        roll = random.randint(1, 20)
        save_bonus = self.get_save_bonus(ability)
        total = roll + save_bonus
        
        success = total >= dc
        return success

    def turn(self, target=None, round_number: int = 0, combat=None) -> None:
        """
        Execute monster's turn in combat.
        
        Handles different AI behaviors like 'caster'.
        
        Args:
            target: Target to attack (if any)
            round_number: The current round number (unused by monster)
            combat: The combat instance for logging
        """
        # Handle prone condition first
        if self.prone:
            self.prone = False
            if combat: combat.log(f"{self.name} stands up from prone")
            return
        
        # No target, nothing else to do
        if target is None:
            return

        # Support AI Logic
        if self.ai_behavior == 'support' and self.spells and combat:
            injured_allies = combat._get_injured_allies(combat.get_combatant(self))
            if injured_allies:
                # Find the most injured ally
                heal_target = min(injured_allies, key=lambda ally: ally.current_hp)
                # Find a healing spell
                healing_spell = next((s for s in self.spells.known_spells if s.name == "Cure Wounds"), None)
                if healing_spell and self.spells.has_slot(healing_spell.slot):
                    if combat: combat.log(f"{self.name} casts {healing_spell.name} on {heal_target.name}")
                    self.spells.cast(healing_spell, target=heal_target.entity)
                    return

        # Caster AI Logic
        if self.ai_behavior == 'caster' and self.spells:
            castable_spells = []
            for spell in self.spells.known_spells:
                if self.spells.has_slot(spell.slot):
                    castable_spells.append(spell)
            
            if castable_spells:
                # Find the spell with the highest level among castable spells
                spell_to_cast = max(castable_spells, key=lambda s: s.slot)
                
                if combat: combat.log(f"{self.name} casts {spell_to_cast.name} at {target.name}")
                self.spells.cast(spell_to_cast, target=target)
                return

        # Default action: basic attack
        self._basic_attack(target, combat=combat)

    def _basic_attack(self, target, combat=None) -> None:
        """
        Perform a basic melee attack.
        
        Uses STR-based attack with proficiency bonus.
        Deals 1d6 + STR modifier piercing damage.
        
        Args:
            target: Target to attack
            combat: The combat instance for logging
        """
        to_hit_bonus = self.mod('str') + self.prof_bonus
        roll = do_roll(disadv=self.poisoned)
        
        if roll + to_hit_bonus >= target.ac:
            # Hit - calculate damage
            damage_roll = random.randint(1, 6)
            str_mod = self.mod('str')
            damage = max(1, damage_roll + str_mod)  # Minimum 1 damage
            
            if combat: combat.log(f"{self.name} hits {target.name} for {damage} piercing damage")
            
            target.apply_damage(damage, 'piercing', self.name)
        else:
            if combat: combat.log(f"{self.name} misses {target.name}")

    def grapple(self) -> None:
        """Mark monster as grappled."""
        self.grappled = True

    def knock_prone(self) -> None:
        """Knock monster prone."""
        self.prone = True

    def is_alive(self) -> bool:
        """
        Check if monster is still alive.
        
        Returns:
            True if HP > 0, False otherwise
        """
        return self.hp > 0

    def is_bloodied(self) -> bool:
        """
        Check if monster is bloodied (below half HP).
        
        Returns:
            True if HP <= max_HP/2
        """
        return self.hp <= self.max_hp // 2

    def __str__(self) -> str:
        """String representation showing name."""
        return self.name

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"BaseMonster(name='{self.name}', ac={self.ac}, "
            f"hp={self.hp}/{self.max_hp})"
        )

    def copy(self):
        """Returns a copy of the monster."""
        import copy
        return copy.deepcopy(self)
