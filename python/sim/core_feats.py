"""
Core feats and weapon mastery mechanics for D&D 5e.

This module implements class level tracking, weapon masteries (Vex, Topple, Graze),
and the feat system for character customization.
"""
from typing import Optional

import sim.feat
import sim.spells


class ClassLevels(sim.feat.Feat):
    """
    Feat that grants class levels and optional spellcasting progression.
    
    This feat is used to track multiclassing and add spellcaster levels
    to a character's progression.
    
    Attributes:
        class_name: Name of the class (e.g., "Fighter", "Wizard")
        level: Number of levels in this class
        spellcaster: Optional spellcaster type for spell slot progression
    """
    
    def __init__(
        self,
        name: str,
        level: int,
        spellcaster: Optional["sim.spells.Spellcaster"] = None,
    ):
        """
        Initialize class levels feat.
        
        Args:
            name: Class name
            level: Number of levels to grant
            spellcaster: Spellcaster type (if applicable)
            
        Raises:
            ValueError: If level is not positive
        """
        if level < 1:
            raise ValueError(f"Level must be positive, got {level}")
        
        self.class_name = name
        self.level = level
        self.spellcaster = spellcaster

    def apply(self, character) -> None:
        """
        Apply class levels to character.
        
        Args:
            character: Character to apply levels to
        """
        super().apply(character)
        character.add_class_level(self.class_name, self.level)
        
        if self.spellcaster is not None:
            character.spells.add_spellcaster_level(self.spellcaster, self.level)


class Vex(sim.feat.Feat):
    """
    Weapon Mastery: Vex.
    
    When you hit with a Vex weapon, your next attack against that target
    has advantage. This advantage is consumed when used or on short rest.
    
    Attributes:
        vexing: Whether advantage is currently available
    """
    
    def __init__(self) -> None:
        """Initialize Vex mastery with no active advantage."""
        self.vexing = False

    def short_rest(self) -> None:
        """Reset vexing status on short rest."""
        self.vexing = False

    def attack_roll(self, args) -> None:
        """
        Grant advantage if vexing is active.
        
        Args:
            args: AttackRollArgs containing attack information
        """
        if self.vexing:
            args.adv = True
            self.vexing = False

    def attack_result(self, args) -> None:
        """
        Mark vexing as active on successful Vex weapon hit.
        
        Args:
            args: AttackResultArgs containing hit/miss information
        """
        weapon = args.attack.weapon
        
        # Check all conditions for Vex to activate
        if not weapon:
            return
        
        if not args.hits():
            return
            
        if weapon.mastery != "Vex":
            return
            
        if "Vex" not in self.character.masteries:
            return
        
        # All conditions met - activate vexing
        self.vexing = True


class Topple(sim.feat.Feat):
    """
    Weapon Mastery: Topple.
    
    When you hit with a Topple weapon, the target must succeed on a
    Strength saving throw or be knocked prone.
    """
    
    def attack_result(self, args) -> None:
        """
        Attempt to knock target prone on hit with Topple weapon.
        
        Args:
            args: AttackResultArgs containing hit/miss and target information
        """
        weapon = args.attack.weapon
        
        # Early returns for conditions not met
        if not weapon:
            return
        
        if args.misses():
            return
        
        if weapon.mastery != "Topple":
            return
            
        if "Topple" not in self.character.masteries:
            return
        
        # All conditions met - attempt to knock prone
        target = args.attack.target
        mod = weapon.mod(self.character)
        dc = self.character.dc(mod)
        
        if not target.save("str", dc):
            target.knock_prone()


class Graze(sim.feat.Feat):
    """
    Weapon Mastery: Graze.
    
    When you miss with a Graze weapon, you still deal damage equal to
    your ability modifier (minimum 0 damage).
    """
    
    def attack_result(self, args) -> None:
        """
        Apply graze damage on miss with Graze weapon.
        
        Args:
            args: AttackResultArgs containing hit/miss and weapon information
        """
        weapon = args.attack.weapon
        
        # Early returns for conditions not met
        if not weapon:
            return
        
        if not args.misses():
            return
        
        if weapon.mastery != "Graze":
            return
            
        if "Graze" not in self.character.masteries:
            return
        
        # All conditions met - apply graze damage
        mod = weapon.mod(self.character)
        modifier_value = self.character.mod(mod)
        
        # Graze damage is ability modifier, minimum 0
        graze_damage = max(0, modifier_value)
        
        if graze_damage > 0:
            args.attack.target.apply_damage(
                source="Graze",
                damage=graze_damage,
                damage_type=weapon.damage_type
            )
