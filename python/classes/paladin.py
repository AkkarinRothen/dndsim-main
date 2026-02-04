"""
Paladin class implementation for D&D 5e combat simulator.

This module implements Paladin class features including Divine Smite,
Channel Divinity, Radiant Strikes, and the Oath of Devotion subclass.
"""

from typing import List, Optional
from enum import IntEnum

import sim.core_feats
from util.util import get_magic_weapon, apply_asi_feats
from feats.fighting_style import TwoWeaponFighting, GreatWeaponFighting
from feats.epic_boons import IrresistibleOffense
from feats import (
    ASI,
    AttackAction,
    GreatWeaponMaster,
    WeaponMasteries,
    AddResource,
)
from weapons import Greatsword, Shortsword, Scimitar
from spells.paladin import DivineFavor, DivineSmite
from sim.spells import Spellcaster

import sim.weapons
import sim.feat
import sim.character
import sim.target


# ============================================================================
# CONSTANTS
# ============================================================================

class PaladinLevels(IntEnum):
    """Key level milestones for Paladin class features."""
    DIVINE_SMITE = 2
    CHANNEL_DIVINITY_1 = 3
    EXTRA_ATTACK = 5
    RADIANT_STRIKES = 11


class DevotionLevels(IntEnum):
    """Key level milestones for Oath of Devotion subclass."""
    SACRED_WEAPON = 3


# Radiant Strikes damage dice
RADIANT_STRIKES_DICE = [8]

# Default ability scores for Paladin (Str and Cha focused)
DEFAULT_PALADIN_STATS = [17, 10, 10, 10, 10, 16]


# ============================================================================
# CORE PALADIN FEATURES
# ============================================================================

class PaladinLevel(sim.core_feats.ClassLevels):
    """
    Represents Paladin class levels and spellcasting progression.
    
    Paladins are half-casters, gaining spell slots more slowly than
    full spellcasters but faster than non-casters.
    """
    
    def __init__(self, level: int):
        """
        Initialize Paladin class levels.
        
        Args:
            level: Character level (1-20)
        """
        super().__init__(
            name="Paladin",
            level=level,
            spellcaster=Spellcaster.HALF
        )


class DivineSmiteFeat(sim.feat.Feat):
    """
    Level 2 Paladin feature: Divine Smite.
    
    When you hit with a melee weapon attack, you can expend a spell slot
    to deal radiant damage to the target. The damage increases with
    higher-level spell slots and critical hits.
    
    Strategy: Use highest available spell slot for maximum damage.
    """
    
    def attack_result(self, args) -> None:
        """
        Trigger Divine Smite on successful hits.
        
        Args:
            args: Attack result arguments
        """
        # Only smite on hits
        if args.misses():
            return
        
        # Check for available spell slots
        slot = self.character.spells.highest_slot()
        if slot >= 1 and self.character.use_bonus("DivineSmite"):
            # Cast Divine Smite using highest slot
            self.character.spells.cast(
                DivineSmite(slot=slot, crit=args.crit),
                target=args.attack.target
            )


class RadiantStrikes(sim.feat.Feat):
    """
    Level 11 Paladin feature: Radiant Strikes.
    
    Your attacks are infused with divine energy. Once on each of your turns,
    when you hit with a melee weapon attack, you can deal an extra 1d8
    radiant damage to the target.
    
    This provides consistent extra damage without resource expenditure.
    """
    
    def attack_result(self, args) -> None:
        """
        Add radiant damage to successful attacks.
        
        Args:
            args: Attack result arguments
        """
        if args.hits():
            args.add_damage(
                source="RadiantStrikes",
                dice=RADIANT_STRIKES_DICE
            )


class DivineFavorFeat(sim.feat.Feat):
    """
    Automated Divine Favor spell management.
    
    Casts Divine Favor at the start of combat if not concentrating
    on another spell. Divine Favor adds 1d4 radiant damage to weapon
    attacks while concentrating.
    """
    
    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Cast Divine Favor if beneficial and possible.
        
        Args:
            target: Combat target
        """
        # Don't interrupt existing concentration
        if self.character.spells.is_concentrating():
            return
        
        # Get lowest available spell slot (Divine Favor is efficient)
        slot = self.character.spells.lowest_slot()
        
        # Cast if we have slots available
        if slot >= 1 and self.character.use_bonus("DivineFavor"):
            self.character.spells.cast(DivineFavor(slot))


# ============================================================================
# OATH OF DEVOTION SUBCLASS FEATURES
# ============================================================================

class SacredWeapon(sim.feat.Feat):
    """
    Oath of Devotion Level 3 feature: Sacred Weapon (Channel Divinity).
    
    As a bonus action, you can imbue one weapon you're holding with
    positive energy. For 1 minute, you add your Charisma modifier to
    attack rolls made with that weapon (minimum bonus of +1).
    
    Uses one Channel Divinity charge and recharges on short rest.
    """
    
    def __init__(self):
        """Initialize Sacred Weapon tracking."""
        super().__init__()
        self.enabled: bool = False

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Activate Sacred Weapon at the start of combat if available.
        
        Args:
            target: Combat target
        """
        # Activate if not already active and Channel Divinity available
        if not self.enabled and self.character.resources['Channel Divinity'].use(detail="Sacred Weapon", target=target):
            self.enabled = True

    def attack_roll(self, args) -> None:
        """
        Add Charisma modifier to attack rolls while Sacred Weapon is active.
        
        Args:
            args: Attack roll arguments
        """
        if self.enabled:
            args.situational_bonus += self.character.mod("cha")


# ============================================================================
# FEAT BUILDERS
# ============================================================================

def paladin_feats(
    level: int,
    masteries: List["sim.weapons.WeaponMastery"],
    fighting_style: "sim.feat.Feat",
    asis: Optional[List["sim.feat.Feat"]] = None,
) -> List["sim.feat.Feat"]:
    """
    Build the standard Paladin feat list for a given level.
    
    Args:
        level: Character level (1-20)
        masteries: Weapon masteries to apply
        fighting_style: Fighting style feat
        asis: ASI/feat choices at appropriate levels
        
    Returns:
        List of Paladin class feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 1: Class basics
    if level >= 1:
        feats.append(PaladinLevel(level))
        feats.append(WeaponMasteries(masteries))
    
    # Level 2: Fighting Style and Divine Smite
    if level >= PaladinLevels.DIVINE_SMITE:
        feats.append(fighting_style)
        feats.append(DivineSmiteFeat())
    
    # Level 3: Channel Divinity
    if level >= PaladinLevels.CHANNEL_DIVINITY_1:
        feats.append(AddResource(name='Channel Divinity', uses=1, short_rest=True))
    
    # Level 11: Radiant Strikes
    if level >= PaladinLevels.RADIANT_STRIKES:
        feats.append(RadiantStrikes())
    
    # Apply ASIs/Feats
    apply_asi_feats(level=level, feats=feats, asis=asis)
    
    return feats


def devotion_paladin_feats(level: int) -> List["sim.feat.Feat"]:
    """
    Build Oath of Devotion subclass feat list.
    
    Args:
        level: Character level (3-20)
        
    Returns:
        List of Devotion Paladin subclass feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 3: Sacred Weapon
    if level >= DevotionLevels.SACRED_WEAPON:
        feats.append(SacredWeapon())
    
    # Note: Other Devotion features (Aura of Devotion, etc.) 
    # are not implemented as they're defensive/support focused
    
    return feats


# ============================================================================
# CHARACTER CLASSES
# ============================================================================

class DevotionPaladin(sim.character.Character):
    """
    Oath of Devotion Paladin.
    
    A righteous warrior who combines martial prowess with divine magic.
    Supports both two-weapon fighting and great weapon fighting styles.
    
    The Devotion Paladin excels at:
    - Burst damage via Divine Smite
    - Consistent radiant damage from class features
    - Enhanced accuracy through Sacred Weapon
    """
    
    def __init__(self, level: int, use_twf: bool = False, **kwargs):
        """
        Initialize Devotion Paladin.
        
        Args:
            level: Character level (1-20)
            use_twf: Use Two-Weapon Fighting instead of Great Weapon Fighting
            **kwargs: Additional character initialization arguments
        """
        self.name = "DevotionPaladin"
        magic_weapon = get_magic_weapon(level)
        feats: List["sim.feat.Feat"] = []
        
        # Add Divine Favor automation
        feats.append(DivineFavorFeat())
        
        # Configure build based on fighting style
        if use_twf:
            # Two-Weapon Fighting build
            masteries: List["sim.weapons.WeaponMastery"] = ["Vex", "Nick"]
            fighting_style: "sim.feat.Feat" = TwoWeaponFighting()
            weapon: "sim.weapons.Weapon" = Shortsword(magic_bonus=magic_weapon)
            nick_attacks = [Scimitar(magic_bonus=magic_weapon)]
        else:
            # Great Weapon Fighting build (default)
            masteries = ["Graze", "Topple"]
            fighting_style = GreatWeaponFighting()
            weapon = Greatsword(magic_bonus=magic_weapon)
            nick_attacks = []
        
        # Configure attacks based on level
        if level >= PaladinLevels.EXTRA_ATTACK:
            attacks = 2 * [weapon]
        else:
            attacks = [weapon]
        
        # Setup attack action
        feats.append(AttackAction(attacks=attacks, nick_attacks=nick_attacks))
        
        # Determine first ASI/Feat
        first_feat = (
            ASI(["str", "con"])  # TWF benefits from survivability
            if use_twf
            else GreatWeaponMaster(weapon)  # GWF wants damage
        )
        
        # Build Paladin progression
        feats.extend(
            paladin_feats(
                level,
                masteries=masteries,
                fighting_style=fighting_style,
                asis=[
                    first_feat,
                    ASI(["str"]),           # Boost primary stat
                    ASI(["cha"]),           # Boost spellcasting
                    ASI(["cha"]),           # More spellcasting
                    IrresistibleOffense("str"),  # Epic boon
                ],
            )
        )
        
        # Add Devotion subclass features
        feats.extend(devotion_paladin_feats(level))
        
        # Initialize character
        # Stats: Str for attacks, Cha for spells and Sacred Weapon
        super().__init__(
            name=self.name,
            level=level,
            stats=DEFAULT_PALADIN_STATS,
            base_feats=feats,
            spellcaster=sim.spells.Spellcaster.HALF,
            spell_mod="cha",  # Charisma-based spellcasting
        )
