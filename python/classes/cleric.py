"""
Cleric class implementation for D&D 5e combat simulator.

This module implements Cleric class features including full spellcasting,
Channel Divinity, Blessed Strikes, and the War Domain subclass.
"""

from typing import List, Optional
from enum import IntEnum

from util.util import get_magic_weapon, apply_asi_feats
from sim.spells import Spellcaster
from feats import ASI, AddResource
from spells.cleric import (
    SpiritGuardians,
    TollTheDead,
    InflictWounds,
    GuardianOfFaith,
)
from spells.summons import SummonCelestial
from weapons import Warhammer

import sim.core_feats
import sim.weapons
import sim.spells
import sim.character
import sim.target
import sim.feat


# ============================================================================
# CONSTANTS
# ============================================================================

class ClericLevels(IntEnum):
    """Key level milestones for Cleric class features."""
    CHANNEL_DIVINITY_1 = 2
    CHANNEL_DIVINITY_2 = 6
    BLESSED_STRIKES_1 = 7
    BLESSED_STRIKES_2 = 14
    CHANNEL_DIVINITY_3 = 18


class WarDomainLevels(IntEnum):
    """Key level milestones for War Domain subclass."""
    WAR_PRIEST = 3


# Blessed Strikes dice by level
BLESSED_STRIKES_DICE = {
    7: 1,   # 1d8 radiant damage
    14: 2,  # 2d8 radiant damage
}

# Spell slot thresholds for spell selection
SUMMON_CELESTIAL_SLOT = 5
SPIRIT_GUARDIANS_SLOT = 3
GUARDIAN_OF_FAITH_SLOT = 4
INFLICT_WOUNDS_SLOT = 1

# Default ability scores for Cleric (Wis primary, Str secondary for War Domain)
DEFAULT_CLERIC_STATS = [15, 10, 10, 10, 17, 10]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_blessed_strikes_dice(level: int) -> int:
    """
    Get number of Blessed Strikes dice based on level.
    
    Args:
        level: Cleric level (7-20)
        
    Returns:
        Number of d8 dice for Blessed Strikes
    """
    for threshold in sorted(BLESSED_STRIKES_DICE.keys(), reverse=True):
        if level >= threshold:
            return BLESSED_STRIKES_DICE[threshold]
    return 1  # Default for level 7


def num_channel_divinity(level: int) -> int:
    """
    Get the number of Channel Divinity uses per short rest for a given Cleric level.
    
    Args:
        level: Cleric level (1-20)
        
    Returns:
        Number of Channel Divinity uses.
    """
    if level >= 18:
        return 3
    elif level >= 6:
        return 2
    elif level >= 2:
        return 1
    return 0


# ============================================================================
# CORE CLERIC FEATURES
# ============================================================================

class ClericLevel(sim.core_feats.ClassLevels):
    """
    Represents Cleric class levels and full spellcasting progression.
    
    Clerics are full spellcasters, gaining the maximum spell slots
    for their level and having access to their entire spell list.
    """
    
    def __init__(self, level: int):
        """
        Initialize Cleric class levels.
        
        Args:
            level: Character level (1-20)
        """
        super().__init__(
            name="Cleric",
            level=level,
            spellcaster=Spellcaster.FULL
        )


class ClericAction(sim.feat.Feat):
    """
    Automated Cleric spell selection for optimal DPR.
    
    Prioritizes:
    1. Concentration spells (Summon Celestial, Spirit Guardians)
    2. High-damage non-concentration spells (Guardian of Faith, Inflict Wounds)
    3. Cantrips as fallback (Toll the Dead)
    
    This represents an optimized Cleric focusing on damage output.
    """
    
    def action(self, target: "sim.target.Target") -> None:
        """
        Choose and cast the optimal spell for the current situation.
        
        Args:
            target: The target to attack/affect
        """
        slot = self.character.spells.highest_slot()
        spell: Optional["sim.spells.Spell"] = None
        
        # If not concentrating, prioritize concentration spells
        if not self.character.spells.is_concentrating() and slot >= SPIRIT_GUARDIANS_SLOT:
            if slot >= SUMMON_CELESTIAL_SLOT:
                # Best concentration spell: Summon Celestial
                spell = SummonCelestial(slot)
            elif slot >= SPIRIT_GUARDIANS_SLOT:
                # Second best: Spirit Guardians
                spell = SpiritGuardians(slot)
        else:
            # Already concentrating or no high-level slots
            # Use non-concentration damage spells
            slot = self.character.spells.highest_slot(max_slot=4)
            
            if slot >= GUARDIAN_OF_FAITH_SLOT:
                spell = GuardianOfFaith(slot)
            elif slot >= INFLICT_WOUNDS_SLOT:
                spell = InflictWounds(slot)
            else:
                # No spell slots left, use cantrip
                spell = TollTheDead()
        
        # Cast the chosen spell
        if spell is not None:
            self.character.spells.cast(spell, target)


class BlessedStrikes(sim.feat.Feat):
    """
    Level 7 Cleric feature: Blessed Strikes.
    
    Once on each of your turns when you hit a creature with a weapon attack
    or deal damage with a cantrip, you can deal an extra 1d8 radiant damage
    (2d8 at level 14).
    
    This provides consistent extra damage to the Cleric's attacks.
    """
    
    # Damage type for Blessed Strikes
    DIE_TYPE = 8
    
    def __init__(self, num_dice: int) -> None:
        """
        Initialize Blessed Strikes.
        
        Args:
            num_dice: Number of d8 dice (1 or 2 based on level)
        """
        super().__init__()
        self.num_dice: int = num_dice
        self.used: bool = False

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Reset Blessed Strikes usage at the start of each turn.
        
        Args:
            target: Combat target
        """
        self.used = False

    def attack_result(self, args) -> None:
        """
        Add radiant damage to the first successful attack each turn.
        
        Args:
            args: Attack result arguments
        """
        if args.hits() and not self.used:
            self.used = True
            args.add_damage(
                "BlessedStrikes",
                dice=self.num_dice * [self.DIE_TYPE]
            )


# ============================================================================
# WAR DOMAIN SUBCLASS FEATURES
# ============================================================================

class WarPriest(sim.feat.Feat):
    """
    War Domain Level 3 feature: War Priest.
    
    When you use the Attack action, you can make one weapon attack as
    a bonus action. You can use this feature a number of times equal
    to your Wisdom modifier (minimum of once).
    
    Recharges on short rest.
    """
    
    def __init__(self, weapon: "sim.weapons.Weapon") -> None:
        """
        Initialize War Priest.
        
        Args:
            weapon: Weapon to use for bonus attacks
        """
        super().__init__()
        self.weapon: "sim.weapons.Weapon" = weapon

    def apply(self, character: "sim.character.Character") -> None:
        """
        Apply War Priest resource to the character.
        
        Args:
            character: The character to apply this feat to.
        """
        super().apply(character)
        max_uses = max(1, character.mod('wis'))
        character.add_resource('War Priest', max_uses=max_uses, short_rest=True)

    def after_action(self, target: "sim.target.Target") -> None:
        """
        Make a bonus attack if uses remain.
        
        Args:
            target: Combat target
        """
        if self.character.resources['War Priest'].use(detail="War Priest Attack", target=target) and self.character.use_bonus("WarPriest"):
            self.character.weapon_attack(target, self.weapon)


# ============================================================================
# FEAT BUILDERS
# ============================================================================

def cleric_feats(
    level: int,
    asis: Optional[List["sim.feat.Feat"]] = None
) -> List["sim.feat.Feat"]:
    """
    Build the standard Cleric feat list for a given level.
    
    Args:
        level: Character level (1-20)
        asis: ASI/feat choices at appropriate levels
        
    Returns:
        List of Cleric class feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 1: Class basics
    if level >= 1:
        feats.append(ClericLevel(level))
    
    # Level 2: Channel Divinity
    if level >= ClericLevels.CHANNEL_DIVINITY_1:
        feats.append(AddResource(name='Channel Divinity', uses=num_channel_divinity(level), short_rest=True))
    
    # Level 7+: Blessed Strikes
    if level >= ClericLevels.BLESSED_STRIKES_1:
        num_dice = get_blessed_strikes_dice(level)
        feats.append(BlessedStrikes(num_dice))
    
    # Apply ASIs/Feats
    apply_asi_feats(level=level, feats=feats, asis=asis)
    
    return feats


def war_cleric_feats(
    level: int,
    weapon: "sim.weapons.Weapon"
) -> List["sim.feat.Feat"]:
    """
    Build War Domain subclass feat list.
    
    Args:
        level: Character level (3-20)
        weapon: Weapon to use for War Priest attacks
        
    Returns:
        List of War Domain subclass feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 3: War Priest
    if level >= WarDomainLevels.WAR_PRIEST:
        feats.append(WarPriest(weapon))
    
    # Note: Other War Domain features (Guided Strike, War God's Blessing)
    # could be implemented but are not currently included
    
    return feats


# ============================================================================
# CHARACTER CLASSES
# ============================================================================

class Cleric(sim.character.Character):
    """
    War Domain Cleric.
    
    A divine spellcaster who can also hold their own in melee combat.
    Combines powerful offensive spells with martial prowess.
    
    The War Cleric excels at:
    - Sustained damage through concentration spells
    - Burst damage with high-level spell slots
    - Bonus attacks via War Priest
    - Consistent extra damage from Blessed Strikes
    """
    
    def __init__(self, level: int, name: str = "Cleric") -> None:
        """
        Initialize War Domain Cleric.
        
        Args:
            level: Character level (1-20)
            name: Character's name
        """
        self.name = name
        magic_weapon = get_magic_weapon(level)
        weapon = Warhammer(magic_bonus=magic_weapon)
        feats: List["sim.feat.Feat"] = []
        
        # Build Cleric progression
        # Focus: Wisdom for spells, Strength for melee attacks
        feats.extend(
            cleric_feats(
                level,
                asis=[
                    ASI(["wis"]),        # Boost primary stat first
                    ASI(["wis", "str"]), # Balance spells and attacks
                    ASI(["str"]),        # More attack power
                    ASI(["str"]),        # Maximize attack stat
                ],
            )
        )
        
        # Add War Domain features
        feats.extend(war_cleric_feats(level, weapon))
        
        # Add automated spell selection
        feats.append(ClericAction())
        
        # Initialize character
        # Stats: Wisdom for spellcasting, Strength for War Priest attacks
        super().__init__(
            name=self.name,
            level=level,
            stats=DEFAULT_CLERIC_STATS,
            base_feats=feats,
            spell_mod="wis",  # Wisdom-based spellcasting
        )
