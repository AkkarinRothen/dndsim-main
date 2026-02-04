"""
Combat target system for D&D 5e simulation.

This module implements the Target class representing generic combat opponents
with level-appropriate AC and saving throws.
"""
from typing import Dict, Optional
from collections import defaultdict
import random

from util.util import prof_bonus
from util.log import log
from util.taggable import Taggable


# Level-appropriate AC values based on DMG guidelines
TARGET_AC = [
    13,  # Level 1
    13,  # Level 2
    13,  # Level 3
    14,  # Level 4
    15,  # Level 5
    15,  # Level 6
    15,  # Level 7
    16,  # Level 8
    16,  # Level 9
    17,  # Level 10
    17,  # Level 11
    17,  # Level 12
    18,  # Level 13
    18,  # Level 14
    18,  # Level 15
    18,  # Level 16
    19,  # Level 17
    19,  # Level 18
    19,  # Level 19
    19,  # Level 20
]


class Target(Taggable):
    """
    Generic combat target with level-appropriate defenses.
    
    Provides a standardized opponent for testing and simulation. AC and
    save bonuses scale with level according to DMG guidelines.
    
    Attributes:
        level: Character level this target is designed for
        ac: Armor Class
        prof: Proficiency bonus
        ability: Ability score modifier for saves
        save_bonus: Total saving throw bonus
        dmg: Total damage taken
        stunned: Whether target is stunned
        prone: Whether target is prone
        grappled: Whether target is grappled
        semistunned: Whether target has temporary disadvantage imposed
    """
    
    def __init__(self, level: int, ac: Optional[int] = None, name: str = "Target"):
        """
        Initialize a target appropriate for the given level.
        
        Args:
            level: Character level (1-20)
            ac: Override AC (uses level-appropriate default if None)
            name: Name of the target
            
        Raises:
            ValueError: If level is not 1-20
        """
        if not 1 <= level <= 20:
            raise ValueError(f"Level must be 1-20, got {level}")
        
        super().__init__()
        
        self.level = level
        self.name = name
        
        # Set AC (use override or level-appropriate default)
        if ac is not None:
            self.ac = ac
        else:
            self.ac = TARGET_AC[level - 1]
        
        # Calculate proficiency bonus
        self.prof = prof_bonus(level)
        
        # Calculate ability modifier for saves (scales with tier)
        if level >= 8:
            self.ability = 5  # Tier 2+
        elif level >= 4:
            self.ability = 4  # Early tier 2
        else:
            self.ability = 3  # Tier 1
        
        self.save_bonus = self.prof + self.ability
        
        # Initialize combat state
        self.long_rest()

    def long_rest(self) -> None:
        """
        Take a long rest, resetting damage and conditions.
        """
        self.dmg = 0
        self._dmg_log: Dict[str, int] = defaultdict(int)
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

    def apply_damage(self, damage: int, damage_type: str, source: str) -> None:
        """
        Apply damage to target.
        
        Currently does not implement resistances/vulnerabilities.
        
        Args:
            damage: Amount of damage
            damage_type: Type of damage (not currently used)
            source: Source of damage (for logging)
        """
        self.dmg += damage
        self._dmg_log[source] += damage

    def log_damage_sources(self) -> None:
        """
        Log all damage sources and total to combat log.
        """
        for source, damage in self._dmg_log.items():
            log.record(f"Damage ({source})", damage)
        log.record("Damage (Total)", self.dmg)

    def save(self, ability: str, dc: int) -> bool:
        """
        Make a saving throw.
        
        Args:
            ability: Ability to save with ('str', 'dex', 'con', etc.)
            dc: Difficulty Class to beat
            
        Returns:
            True if save succeeded, False otherwise
            
        Note:
            Currently uses same bonus for all saves. Real monsters
            would have different bonuses for different saves.
        """
        roll = random.randint(1, 20)
        total = roll + self.save_bonus
        
        success = total >= dc
        log.output(
            lambda: f"Target {ability.upper()} save: {roll} + {self.save_bonus} "
                    f"= {total} vs DC {dc} ({'SUCCESS' if success else 'FAIL'})"
        )
        
        return success

    def turn(self) -> None:
        """
        Execute target's turn.
        
        Currently just handles standing up from prone.
        Real implementation would include attacks, spells, etc.
        """
        if self.prone:
            self.prone = False
            log.output(lambda: "Target stands up from prone")

    def grapple(self) -> None:
        """Mark target as grappled."""
        self.grappled = True
        log.output(lambda: "Target is grappled")

    def knock_prone(self) -> None:
        """Knock target prone."""
        log.record("Knocked prone", 1)
        self.prone = True

    def is_bloodied(self) -> bool:
        """
        Check if target has taken significant damage.
        
        "Bloodied" typically means at/below half HP in D&D, but since
        Target doesn't track HP, we use a damage threshold.
        
        Returns:
            True if damage exceeds expected HP for level
        """
        # Rough HP estimate: 10 + (level * 6)
        estimated_hp = 10 + (self.level * 6)
        return self.dmg >= estimated_hp // 2

    def __str__(self) -> str:
        """String representation."""
        return self.name

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Target(name='{self.name}', level={self.level}, ac={self.ac}, "
            f"damage_taken={self.dmg})"
        )



def create_low_ac_target(level: int) -> Target:
    """
    Create a target with lower than normal AC.
    
    Useful for testing guaranteed hits.
    
    Args:
        level: Character level
        
    Returns:
        Target with AC 5
    """
    return Target(level, ac=5)


def create_high_ac_target(level: int) -> Target:
    """
    Create a target with very high AC.
    
    Useful for testing guaranteed misses.
    
    Args:
        level: Character level
        
    Returns:
        Target with AC 25
    """
    return Target(level, ac=25)


def create_boss_target(level: int) -> Target:
    """
    Create a tougher target appropriate for a boss fight.
    
    Args:
        level: Character level
        
    Returns:
        Target with AC +2 above normal for level
    """
    normal_ac = TARGET_AC[level - 1]
    return Target(level, ac=normal_ac + 2)
