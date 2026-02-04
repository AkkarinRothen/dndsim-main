"""
Barbarian class implementation for D&D 5e combat simulator.

This module implements Barbarian class features including Rage, Reckless Attack,
Brutal Strike, and the Berserker subclass specialization.
"""

from typing import List, Optional
from enum import IntEnum

import sim.core_feats
from util.util import get_magic_weapon, apply_asi_feats
from feats.epic_boons import IrresistibleOffense
from feats.origin import SavageAttacker
from feats import (
    ASI,
    GreatWeaponMaster,
    PolearmMaster,
    AttackAction,
    WeaponMasteries,
)
from weapons import Glaive, Greatsword, GlaiveButt

import sim.feat
import sim.character
import sim.weapons


# ============================================================================
# CONSTANTS
# ============================================================================

class BarbarianLevels(IntEnum):
    """Key level milestones for Barbarian class features."""
    RAGE = 1
    RECKLESS_ATTACK = 2
    EXTRA_ATTACK = 5
    BRUTAL_STRIKE = 9
    RAGE_DAMAGE_2 = 9
    RAGE_DAMAGE_3 = 16
    BRUTAL_STRIKE_2 = 17
    PRIMAL_CHAMPION = 20


class BerserkerLevels(IntEnum):
    """Key level milestones for Berserker subclass features."""
    FRENZY = 3
    RETALIATION = 10


# Rage damage bonus by level
RAGE_DAMAGE_BY_LEVEL = {
    1: 2,   # Levels 1-8
    9: 3,   # Levels 9-15
    16: 4,  # Levels 16-20
}

# Number of rages by level
RAGES_BY_LEVEL = {
    1: 2,
    3: 3,
    6: 4,
    12: 5,
    17: 6,
    20: 99, # Unlimited
}

# Brutal Strike dice by level
BRUTAL_STRIKE_DICE = {
    9: 1,   # Levels 9-16
    17: 2,  # Levels 17-20
}

# Primal Champion stat increases
PRIMAL_CHAMPION_STR_BONUS = 4
PRIMAL_CHAMPION_CON_BONUS = 4


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def rage_damage(level: int) -> int:
    """
    Calculate rage damage bonus based on Barbarian level.
    
    Args:
        level: Barbarian level (1-20)
        
    Returns:
        Rage damage bonus
    """
    for threshold in sorted(RAGE_DAMAGE_BY_LEVEL.keys(), reverse=True):
        if level >= threshold:
            return RAGE_DAMAGE_BY_LEVEL[threshold]
    return 2  # Default for level 1


def num_rages(level: int) -> int:
    """
    Get the number of rages per long rest for a given Barbarian level.
    
    Args:
        level: Barbarian level (1-20)
        
    Returns:
        Number of rages.
    """
    for threshold in sorted(RAGES_BY_LEVEL.keys(), reverse=True):
        if level >= threshold:
            return RAGES_BY_LEVEL[threshold]
    return 2 # Default for level 1


def get_brutal_strike_dice(level: int) -> int:
    """
    Get number of Brutal Strike dice based on level.
    
    Args:
        level: Barbarian level (9-20)
        
    Returns:
        Number of d10 dice for Brutal Strike
    """
    for threshold in sorted(BRUTAL_STRIKE_DICE.keys(), reverse=True):
        if level >= threshold:
            return BRUTAL_STRIKE_DICE[threshold]
    return 1  # Default for level 9


# ============================================================================
# CORE BARBARIAN FEATURES
# ============================================================================

class BarbarianLevel(sim.core_feats.ClassLevels):
    """Represents Barbarian class levels and core features."""
    
    def __init__(self, level: int):
        """
        Initialize Barbarian class levels.
        
        Args:
            level: Character level (1-20)
        """
        super().__init__(name="Barbarian", level=level)


class Rage(sim.feat.Feat):
    """
    Level 1 Barbarian feature: Rage.
    
    Enter a rage as a bonus action to gain:
    - Bonus damage on melee attacks using Strength
    - Advantage on Strength checks and saving throws (not implemented)
    - Resistance to physical damage (not implemented)
    
    Rage damage increases at levels 9 and 16.
    """
    
    def __init__(self, dmg: int, max_rages: int):
        """
        Initialize Rage feature.
        
        Args:
            dmg: Rage damage bonus (2/3/4 based on level)
            max_rages: Maximum number of rages per long rest
        """
        super().__init__()
        self.raging: bool = False
        self.dmg: int = dmg
        self.max_rages: int = max_rages

    def apply(self, character: "sim.character.Character") -> None:
        """Apply Rage resource to the character."""
        super().apply(character)
        character.add_resource('Rage', max_uses=self.max_rages, short_rest=False)

    def before_action(self, target: "sim.target.Target") -> None:
        """
        Enter rage if not already raging and resources are available.
        
        Args:
            target: Combat target
        """
        if not self.raging and self.character.use_bonus("Rage"):
            if self.character.resources['Rage'].use(detail="Enter Rage", target=target):
                self.raging = True

    def attack_result(self, args) -> None:
        """
        Add rage damage to successful attacks while raging.
        
        Args:
            args: Attack result arguments
        """
        if args.hits() and self.raging:
            args.add_damage(source="Rage", damage=self.dmg)


class RecklessAttack(sim.feat.Feat):
    """
    Level 2 Barbarian feature: Reckless Attack.
    
    When making your first attack on your turn, you can gain advantage
    on all melee weapon attacks using Strength this turn.
    
    Note: The downside (granting advantage to attacks against you) is not
    implemented as it's not relevant to DPR calculations.
    """
    
    def __init__(self):
        """Initialize Reckless Attack tracking."""
        super().__init__()
        self.enabled: bool = False

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Enable Reckless Attack at the start of turn.
        
        Args:
            target: Combat target
        """
        self.enabled = True

    def attack_roll(self, args) -> None:
        """
        Grant advantage on attack rolls while Reckless Attack is active.
        
        Args:
            args: Attack roll arguments
        """
        if self.enabled:
            args.adv = True

    def end_turn(self, target: "sim.target.Target") -> None:
        """
        Disable Reckless Attack at end of turn.
        
        Args:
            target: Combat target
        """
        self.enabled = False


class BrutalStrike(sim.feat.Feat):
    """
    Level 9 Barbarian feature: Brutal Strike.
    
    When you have advantage on an attack roll, you can forgo advantage
    to add extra damage dice (1d10 at level 9, 2d10 at level 17) and
    apply a special effect (not fully implemented).
    """
    
    # Die type for Brutal Strike damage
    DIE_TYPE = 10
    
    def __init__(self, num_dice: int):
        """
        Initialize Brutal Strike.
        
        Args:
            num_dice: Number of d10 dice to add (1 or 2)
        """
        super().__init__()
        self.num_dice: int = num_dice
        self.used: bool = False

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Reset Brutal Strike usage at start of turn.
        
        Args:
            target: Combat target
        """
        self.used = False

    def attack_roll(self, args) -> None:
        """
        Trade advantage for Brutal Strike if beneficial.
        
        Args:
            args: Attack roll arguments
        """
        if not self.used and args.adv:
            args.adv = False  # Forgo advantage
            args.attack.add_tag("brutal_strike")
            self.used = True

    def attack_result(self, args) -> None:
        """
        Add Brutal Strike damage on tagged attacks that hit.
        
        Args:
            args: Attack result arguments
        """
        if args.hits() and args.attack.has_tag("brutal_strike"):
            args.add_damage(
                source="BrutalStrike",
                dice=self.num_dice * [self.DIE_TYPE]
            )


class PrimalChampion(sim.feat.Feat):
    """
    Level 20 Barbarian feature: Primal Champion.
    
    Increases Strength and Constitution scores and maximums by 4.
    This represents the pinnacle of physical perfection.
    """
    
    def apply(self, character: "sim.character.Character") -> None:
        """
        Apply Primal Champion stat increases.
        
        Args:
            character: The character to enhance
        """
        super().apply(character)
        
        # Increase maximum scores
        character.increase_stat_max("str", PRIMAL_CHAMPION_STR_BONUS)
        character.increase_stat_max("con", PRIMAL_CHAMPION_CON_BONUS)
        
        # Increase current scores
        character.increase_stat("str", PRIMAL_CHAMPION_STR_BONUS)
        character.increase_stat("con", PRIMAL_CHAMPION_CON_BONUS)


# ============================================================================
# BERSERKER SUBCLASS FEATURES
# ============================================================================

class Frenzy(sim.feat.Feat):
    """
    Berserker Level 3 feature: Frenzy.
    
    While raging, the first time you hit with a melee attack on your turn,
    you deal extra damage equal to your rage damage bonus (in d6s).
    
    Example: At level 3-8 (rage bonus +2), deal 2d6 extra damage.
    """
    
    # Die type for Frenzy damage
    DIE_TYPE = 6
    
    def __init__(self, num_dice: int):
        """
        Initialize Frenzy feature.
        
        Args:
            num_dice: Number of d6 dice (equals rage damage bonus)
        """
        super().__init__()
        self.used: bool = False
        self.num_dice: int = num_dice

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Reset Frenzy usage at the start of turn.
        
        Args:
            target: Combat target
        """
        self.used = False

    def attack_result(self, args) -> None:
        """
        Add Frenzy damage to the first hit each turn.
        
        Args:
            args: Attack result arguments
        """
        if args.hits() and not self.used:
            self.used = True
            args.add_damage(
                source="Berserker",
                dice=self.num_dice * [self.DIE_TYPE]
            )


class Retaliation(sim.feat.Feat):
    """
    Berserker Level 10 feature: Retaliation.
    
    When you take damage from a creature within your weapon's reach,
    you can use your reaction to make a melee weapon attack against them.
    
    Simplified for simulation: Make an extra attack during enemy turn.
    """
    
    def __init__(self, weapon: "sim.weapons.Weapon"):
        """
        Initialize Retaliation.
        
        Args:
            weapon: Weapon to use for retaliation attacks
        """
        super().__init__()
        self.weapon: "sim.weapons.Weapon" = weapon

    def enemy_turn(self, target: "sim.target.Target") -> None:
        """
        Make a retaliation attack during the enemy's turn.
        
        Args:
            target: The enemy that attacked you
        """
        self.character.weapon_attack(target, weapon=self.weapon)


# ============================================================================
# FEAT BUILDERS
# ============================================================================

def barbarian_feats(
    level: int,
    asis: Optional[List["sim.feat.Feat"]] = None
) -> List["sim.feat.Feat"]:
    """
    Build the standard Barbarian feat list for a given level.
    
    Args:
        level: Character level (1-20)
        asis: ASI/feat choices at appropriate levels
        
    Returns:
        List of Barbarian class feats
    """
    rage_dmg = rage_damage(level)
    feats: List["sim.feat.Feat"] = []
    
    # Level 1: Core features
    if level >= BarbarianLevels.RAGE:
        feats.append(BarbarianLevel(level))
        feats.append(WeaponMasteries(["Graze", "Topple"]))
        feats.append(Rage(dmg=rage_dmg, max_rages=num_rages(level)))
    
    # Level 2: Reckless Attack
    if level >= BarbarianLevels.RECKLESS_ATTACK:
        feats.append(RecklessAttack())
    
    # Level 9+: Brutal Strike
    if level >= BarbarianLevels.BRUTAL_STRIKE:
        num_dice = get_brutal_strike_dice(level)
        feats.append(BrutalStrike(num_dice=num_dice))
    
    # Level 20: Primal Champion
    if level >= BarbarianLevels.PRIMAL_CHAMPION:
        feats.append(PrimalChampion())
    
    # Apply ASIs/Feats
    apply_asi_feats(level, feats, asis)
    
    return feats


def berserker_feats(
    level: int,
    weapon: "sim.weapons.Weapon"
) -> List["sim.feat.Feat"]:
    """
    Build Berserker subclass feat list.
    
    Args:
        level: Character level (3-20)
        weapon: Weapon to use for Retaliation
        
    Returns:
        List of Berserker subclass feats
    """
    rage_dmg = rage_damage(level)
    feats: List["sim.feat.Feat"] = []
    
    # Level 3: Frenzy
    if level >= BerserkerLevels.FRENZY:
        feats.append(Frenzy(num_dice=rage_dmg))
    
    # Level 10: Retaliation
    if level >= BerserkerLevels.RETALIATION:
        feats.append(Retaliation(weapon))
    
    return feats


# ============================================================================
# CHARACTER CLASSES
# ============================================================================

class PolearmBarbarian(sim.character.Character):
    """
    Polearm Master Berserker Barbarian build.
    
    Uses Glaive with Polearm Master for bonus action attacks.
    Focuses on maximizing attacks while raging.
    """
    
    def __init__(self, level: int):
        """
        Initialize Polearm Master Barbarian.
        
        Args:
            level: Character level (1-20)
        """
        self.name = "Polearm Barbarian"
        magic_weapon = get_magic_weapon(level)
        feats: List["sim.feat.Feat"] = []
        
        # Primary weapon: Glaive
        weapon = Glaive(magic_bonus=magic_weapon)
        
        # Attack action (Extra Attack at level 5)
        attacks = [weapon, weapon] if level >= BarbarianLevels.EXTRA_ATTACK else [weapon]
        feats.append(AttackAction(attacks=attacks))
        
        # Barbarian progression with Polearm Master
        feats.extend(
            barbarian_feats(
                level,
                asis=[
                    PolearmMaster(weapon, bonus_action_weapon=GlaiveButt()),
                    GreatWeaponMaster(weapon), # Polearm Master enables GWM attacks
                    ASI(["str"]),  # Pure Strength focus
                    ASI(["dex"]),  # Some AC improvement
                    ASI(["dex"]),
                    IrresistibleOffense("str"),
                ],
            )
        )
        
        # Origin feat
        feats.append(SavageAttacker())
        
        # Initialize character with Strength-focused stats
        super().__init__(
            name=self.name,
            level=level,
            stats=[17, 10, 10, 10, 10, 10],  # High Str, average everything else
            base_feats=feats,
        )


class BerserkerBarbarian(sim.character.Character):
    """
    Standard Berserker Barbarian build.
    
    Uses Greatsword with Great Weapon Master for maximum damage.
    The classic raging warrior archetype.
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Berserker Barbarian.
        
        Args:
            level: Character level (1-20)
            **kwargs: Additional character initialization arguments
        """
        self.name = "Berserker Barbarian"
        magic_weapon = get_magic_weapon(level)
        feats: List["sim.feat.Feat"] = []
        
        # Primary weapon: Greatsword
        weapon = Greatsword(magic_bonus=magic_weapon)
        
        # Attack action (Extra Attack at level 5)
        attacks = [weapon, weapon] if level >= BarbarianLevels.EXTRA_ATTACK else [weapon]
        feats.append(AttackAction(attacks=attacks))
        
        # Barbarian progression
        feats.extend(
            barbarian_feats(
                level,
                asis=[
                    GreatWeaponMaster(weapon),
                    ASI(["str"]),  # Pure Strength focus
                    ASI(["dex"]),  # Some AC improvement
                    ASI(["dex"]),
                    IrresistibleOffense("str"),
                ],
            )
        )
        
        # Berserker subclass features
        feats.extend(berserker_feats(level, weapon))
        
        # Origin feat
        feats.append(SavageAttacker())
        
        # Initialize character with Strength-focused stats
        super().__init__(
            name=self.name,
            level=level,
            stats=[17, 10, 10, 10, 10, 10],  # High Str, average everything else
            base_feats=feats,
        )
