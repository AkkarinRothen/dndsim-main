"""
Fighter class implementation for D&D 5e combat simulator.

This module implements Fighter class features, subclasses (Champion, Battlemaster),
and various fighting styles including Great Weapon Fighting and Two-Weapon Fighting.
"""

import random
from typing import List, Optional
from enum import IntEnum

import sim.core_feats
from util.util import get_magic_weapon, apply_asi_feats
from feats.epic_boons import IrresistibleOffense
from feats.fighting_style import TwoWeaponFighting, GreatWeaponFighting
from feats.origin import SavageAttacker
from feats import (
    GreatWeaponMaster,
    ASI,
    PolearmMaster,
    WeaponMasteries,
    DualWielder,
)
from weapons import (
    Glaive,
    Greatsword,
    GlaiveButt,
    Maul,
    Shortsword,
    Scimitar,
    Rapier,
)

import sim.feat
import sim.weapons
import sim.character
import sim.target


# ============================================================================
# CONSTANTS
# ============================================================================

class FighterLevels(IntEnum):
    """Key level milestones for Fighter class features."""
    EXTRA_ATTACK_1 = 5
    EXTRA_ATTACK_2 = 11
    STUDIED_ATTACKS = 13
    ACTION_SURGE_2 = 17
    EXTRA_ATTACK_3 = 20


class ChampionLevels(IntEnum):
    """Key level milestones for Champion subclass features."""
    IMPROVED_CRITICAL = 3
    HEROIC_ADVANTAGE = 10
    SUPERIOR_CRITICAL = 15


class BattlemasterLevels(IntEnum):
    """Key level milestones for Battlemaster subclass features."""
    COMBAT_SUPERIORITY = 3
    IMPROVED_SUPERIORITY_1 = 7
    IMPROVED_SUPERIORITY_2 = 10
    RELENTLESS = 15
    IMPROVED_SUPERIORITY_3 = 18


# Maneuver dice progression
MANEUVER_DICE_BY_LEVEL = {
    3: (4, 8),   # (num_dice, die_size)
    7: (5, 8),
    10: (5, 10),
    15: (6, 10),
    18: (6, 12),
}

# Critical hit thresholds
CRIT_THRESHOLD_IMPROVED = 19
CRIT_THRESHOLD_SUPERIOR = 18

# ASI/Feat schedule for Fighters (gets more than standard classes)
FIGHTER_ASI_LEVELS = [4, 6, 8, 12, 14, 16, 19]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_num_attacks(level: int) -> int:
    """
    Calculate number of attacks for a Fighter based on level.
    
    Args:
        level: Character level (1-20)
        
    Returns:
        Number of attacks per Attack action
        
    Examples:
        >>> get_num_attacks(1)
        1
        >>> get_num_attacks(5)
        2
        >>> get_num_attacks(11)
        3
        >>> get_num_attacks(20)
        4
    """
    if level >= FighterLevels.EXTRA_ATTACK_3:
        return 4
    elif level >= FighterLevels.EXTRA_ATTACK_2:
        return 3
    elif level >= FighterLevels.EXTRA_ATTACK_1:
        return 2
    else:
        return 1


def get_maneuver_stats(level: int) -> tuple[int, int]:
    """
    Get the number and size of superiority dice for a given level.
    
    Args:
        level: Character level (3-20)
        
    Returns:
        Tuple of (number_of_dice, die_size)
    """
    for threshold in sorted(MANEUVER_DICE_BY_LEVEL.keys(), reverse=True):
        if level >= threshold:
            return MANEUVER_DICE_BY_LEVEL[threshold]
    return (4, 8)  # Default for level 3


# ============================================================================
# CORE FIGHTER FEATURES
# ============================================================================

class FighterLevel(sim.core_feats.ClassLevels):
    """Represents Fighter class levels and core features."""
    
    def __init__(self, level: int):
        """
        Initialize Fighter class levels.
        
        Args:
            level: Character level (1-20)
        """
        super().__init__(name="Fighter", level=level)


class StudiedAttacks(sim.feat.Feat):
    """
    Level 13 Fighter feature: Studied Attacks.
    
    When you miss an attack, you gain advantage on your next attack roll.
    This represents learning from mistakes and adapting tactics mid-combat.
    """
    
    def __init__(self) -> None:
        """Initialize Studied Attacks with disabled state."""
        super().__init__()
        self.enabled: bool = False

    def attack_roll(self, args) -> None:
        """
        Apply advantage if enabled from a previous miss.
        
        Args:
            args: Attack roll arguments
        """
        if self.enabled:
            args.adv = True
            self.enabled = False

    def attack_result(self, args) -> None:
        """
        Enable advantage on next attack if this attack missed.
        
        Args:
            args: Attack result arguments
        """
        if args.misses():
            self.enabled = True


class ActionSurge(sim.feat.Feat):
    """
    Level 2 Fighter feature: Action Surge.
    
    Allows taking an additional action on your turn. Recharges on short rest.
    Gains a second use at level 17.
    """
    
    def __init__(self, max_surges: int) -> None:
        """
        Initialize Action Surge.
        
        Args:
            max_surges: Maximum uses per short rest (1 at level 2, 2 at level 17)
        """
        super().__init__()
        self.max_surges: int = max_surges

    def apply(self, character: "sim.character.Character") -> None:
        """
        Apply Action Surge resource to the character.
        
        Args:
            character: The character to apply this feat to.
        """
        super().apply(character)
        character.add_resource('Action Surge', max_uses=self.max_surges, short_rest=True)

    def before_action(self, target: "sim.target.Target") -> None:
        """
        Use Action Surge to gain an additional action if available.
        
        Args:
            target: Combat target
        """
        if self.character.resources['Action Surge'].use(detail="Action Surge", target=target):
            self.character.actions += 1



# ============================================================================
# CHAMPION SUBCLASS FEATURES
# ============================================================================

class ImprovedCritical(sim.feat.Feat):
    """
    Champion feature: Improved/Superior Critical.
    
    Level 3: Critical hits on 19-20
    Level 15: Critical hits on 18-20
    """
    
    def __init__(self, min_crit: int):
        """
        Initialize critical hit threshold.
        
        Args:
            min_crit: Minimum d20 roll for a critical hit (19 or 18)
        """
        super().__init__()
        self.min_crit: int = min_crit

    def attack_roll(self, args) -> None:
        """
        Modify critical hit threshold for attacks.
        
        Args:
            args: Attack roll arguments
        """
        if args.min_crit:
            args.min_crit = min(args.min_crit, self.min_crit)
        else:
            args.min_crit = self.min_crit


class HeroicAdvantage(sim.feat.Feat):
    """
    Champion Level 10 feature: Heroic Advantage.
    
    When you roll lower than 8 on an attack, you can reroll with advantage.
    This ability can be used once per turn.
    """
    
    # Threshold for triggering reroll
    REROLL_THRESHOLD = 8
    
    def __init__(self) -> None:
        """Initialize Heroic Advantage tracking."""
        super().__init__()
        self.used: bool = False

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Reset usage at the start of each turn.
        
        Args:
            target: Combat target
        """
        self.used = False

    def attack_roll(self, args) -> None:
        """
        Grant advantage on low rolls.
        
        Args:
            args: Attack roll arguments
        """
        # Don't apply if already used this turn or if already have advantage
        if self.used or args.adv:
            return
            
        # Handle disadvantage case
        if args.disadv:
            roll = args.roll()
            if roll < self.REROLL_THRESHOLD:
                self.used = True
                args.adv = True
                args.roll1 = random.randint(1, 20)
        else:
            # Normal roll case
            roll = args.roll1
            if roll < self.REROLL_THRESHOLD:
                self.used = True
                args.adv = True


# ============================================================================
# BATTLEMASTER SUBCLASS FEATURES
# ============================================================================

class CombatSuperiority(sim.feat.Feat):
    """
    Battlemaster Level 3 feature: Combat Superiority.
    
    Grants superiority dice that can be used for maneuvers.
    Dice number and size improve at higher levels.
    """
    
    def __init__(self, level: int) -> None:
        """
        Initialize Combat Superiority based on level.
        
        Args:
            level: Character level (determines dice pool and size)
        """
        super().__init__()
        self.level: int = level

    def apply(self, character: "sim.character.Character") -> None:
        """
        Apply superiority dice to the character.
        
        Args:
            character: The character to apply this feat to
        """
        super().apply(character)
        num_dice, die_size = get_maneuver_stats(self.level)
        character.maneuvers.max_dice = num_dice
        character.maneuvers.die = die_size


class Relentless(sim.feat.Feat):
    """
    Battlemaster Level 15 feature: Relentless.
    
    When you roll initiative with no superiority dice remaining,
    you regain one expended die.
    """
    
    def apply(self, character: "sim.character.Character") -> None:
        """
        Enable relentless maneuver dice regeneration.
        
        Args:
            character: The character to apply this feat to
        """
        super().apply(character)
        character.maneuvers.relentless = True


class PrecisionAttack(sim.feat.Feat):
    """
    Battlemaster Maneuver: Precision Attack.
    
    When you make an attack roll, you can add a superiority die
    to improve your chance to hit.
    """
    
    def __init__(self, low: int = 5) -> None:
        """
        Initialize Precision Attack maneuver.
        
        Args:
            low: Minimum d20 roll to trigger precision (default 5)
        """
        super().__init__()
        self.low: int = low

    def attack_roll(self, args) -> None:
        """
        Use superiority die to boost attack roll if needed.
        
        Args:
            args: Attack roll arguments
        """
        # Don't use if already used a maneuver on this attack
        if args.attack.has_tag("used_maneuver"):
            return
            
        # Use precision if we would miss but rolled high enough
        if not args.hits() and args.roll() >= self.low:
            roll = self.character.maneuvers.roll()
            args.situational_bonus += roll
            args.attack.add_tag("used_maneuver")


class TrippingAttack(sim.feat.Feat):
    """
    Battlemaster Maneuver: Tripping Attack.
    
    When you hit with an attack, you can add a superiority die to damage
    and force the target to make a Strength save or be knocked prone.
    """
    
    def attack_result(self, args) -> None:
        """
        Attempt to trip the target on a hit.
        
        Args:
            args: Attack result arguments
        """
        # Only apply on hits
        if args.misses():
            return
            
        # Don't use if already used a maneuver
        if args.attack.has_tag("used_maneuver"):
            return
            
        # Don't waste it if target is already prone
        if args.attack.target.prone:
            return
            
        # Use superiority die
        die = self.character.maneuvers.use()
        if die > 0:
            args.add_damage(source="TrippingAttack", dice=[die])
            
            # Force save to avoid being knocked prone
            if not args.attack.target.save(self.character.dc("str")):
                args.attack.target.knock_prone()
                
            args.attack.add_tag("used_maneuver")


# ============================================================================
# ATTACK ACTIONS
# ============================================================================

class DefaultFighterAction(sim.feat.Feat):
    """
    Standard Fighter attack action with weapon mastery support.
    
    Handles multiple attacks, optional Topple mastery usage,
    and Nick weapon attacks for Two-Weapon Fighting.
    """
    
    def __init__(
        self,
        level: int,
        weapon: "sim.weapons.Weapon",
        topple_weapon: Optional["sim.weapons.Weapon"] = None,
        nick_weapon: Optional["sim.weapons.Weapon"] = None,
    ):
        """
        Initialize Fighter attack action.
        
        Args:
            level: Character level (determines number of attacks)
            weapon: Primary weapon for attacks
            topple_weapon: Optional weapon with Topple mastery
            nick_weapon: Optional light weapon with Nick mastery for bonus attack
        """
        super().__init__()
        self.num_attacks: int = get_num_attacks(level)
        self.weapon: "sim.weapons.Weapon" = weapon
        self.topple_weapon: Optional["sim.weapons.Weapon"] = topple_weapon
        self.nick_weapon: Optional["sim.weapons.Weapon"] = nick_weapon

    def action(self, target: "sim.target.Target") -> None:
        """
        Execute the Fighter's attack sequence.
        
        Uses Topple weapon if target isn't prone and we have attacks remaining.
        Adds Nick weapon attack if available.
        
        Args:
            target: The target to attack
        """
        # Main attacks
        for i in range(self.num_attacks):
            weapon = self.weapon
            
            # Use Topple weapon if beneficial
            if (
                self.topple_weapon is not None
                and not target.prone
                and i < self.num_attacks - 1  # Don't use on last attack
            ):
                weapon = self.topple_weapon
                
            self.character.weapon_attack(target, weapon, tags=["main_action"])
        
        # Nick weapon bonus attack if available
        if self.nick_weapon:
            self.character.weapon_attack(
                target, self.nick_weapon, tags=["main_action", "light"]
            )


# ============================================================================
# FEAT BUILDERS
# ============================================================================

def fighter_feats(
    level: int,
    masteries: List["sim.weapons.WeaponMastery"],
    fighting_style: "sim.feat.Feat",
    asis: Optional[List["sim.feat.Feat"]] = None,
) -> List["sim.feat.Feat"]:
    """
    Build the standard Fighter feat list for a given level.
    
    Args:
        level: Character level (1-20)
        masteries: Weapon masteries to apply
        fighting_style: Fighting style feat
        asis: ASI/feat choices at appropriate levels
        
    Returns:
        List of Fighter feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 1: Class basics
    if level >= 1:
        feats.append(FighterLevel(level))
        feats.append(WeaponMasteries(masteries))
        feats.append(fighting_style)
    
    # Level 2: Action Surge
    if level >= 2:
        max_surges = 2 if level >= FighterLevels.ACTION_SURGE_2 else 1
        feats.append(ActionSurge(max_surges))
    
    # Level 13: Studied Attacks
    if level >= FighterLevels.STUDIED_ATTACKS:
        feats.append(StudiedAttacks())
    
    # Apply ASIs/Feats at Fighter's enhanced schedule
    apply_asi_feats(
        level=level,
        feats=feats,
        asis=asis,
        schedule=FIGHTER_ASI_LEVELS
    )
    
    return feats


def champion_feats(level: int) -> List["sim.feat.Feat"]:
    """
    Build Champion subclass feat list.
    
    Args:
        level: Character level (3-20)
        
    Returns:
        List of Champion subclass feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 3: Improved Critical (19-20)
    # Level 15: Superior Critical (18-20)
    if level >= ChampionLevels.IMPROVED_CRITICAL:
        crit_threshold = (
            CRIT_THRESHOLD_SUPERIOR 
            if level >= ChampionLevels.SUPERIOR_CRITICAL 
            else CRIT_THRESHOLD_IMPROVED
        )
        feats.append(ImprovedCritical(crit_threshold))
    
    # Level 10: Heroic Advantage
    if level >= ChampionLevels.HEROIC_ADVANTAGE:
        feats.append(HeroicAdvantage())
    
    return feats


def battlemaster_feats(level: int) -> List["sim.feat.Feat"]:
    """
    Build Battlemaster subclass feat list (without specific maneuvers).
    
    Args:
        level: Character level (3-20)
        
    Returns:
        List of Battlemaster subclass feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 3: Combat Superiority
    if level >= BattlemasterLevels.COMBAT_SUPERIORITY:
        feats.append(CombatSuperiority(level))
    
    # Level 15: Relentless
    if level >= BattlemasterLevels.RELENTLESS:
        feats.append(Relentless())
    
    return feats


# ============================================================================
# CHARACTER CLASSES
# ============================================================================

class Fighter(sim.character.Character):
    """
    Base Fighter class implementation.
    
    Supports Great Weapon Fighting and Polearm Master builds.
    Can be subclassed for Champion, Battlemaster, etc.
    """
    
    def __init__(
        self,
        level: int,
        use_pam: bool = False,
        subclass_feats: List["sim.feat.Feat"] = [],
        use_topple: bool = True,
        **kwargs
    ):
        """
        Initialize Fighter character.
        
        Args:
            level: Character level (1-20)
            use_pam: Whether to use Polearm Master feat
            subclass_feats: Subclass-specific feats to include
            use_topple: Whether to use Topple weapon mastery
            **kwargs: Additional character initialization arguments
        """
        self.name = "Fighter"
        feats: List["sim.feat.Feat"] = []

        # Determine weapons based on build
        magic_weapon = get_magic_weapon(level)
        if use_pam:
            weapon: "sim.weapons.Weapon" = Glaive(magic_bonus=magic_weapon)
            bonus_weapon = GlaiveButt(magic_bonus=magic_weapon)
        else:
            weapon = Greatsword(magic_bonus=magic_weapon)
            bonus_weapon = None

        # Setup attack action
        topple_weapon = Maul(magic_bonus=magic_weapon) if use_topple else None
        feats.append(DefaultFighterAction(level, weapon, topple_weapon))

        # Origin Feat
        feats.append(SavageAttacker())

        # Add subclass feats
        feats.extend(subclass_feats)
        
        # Standard Fighter progression
        feats.extend(
            fighter_feats(
                level,
                masteries=["Topple", "Graze"],
                fighting_style=GreatWeaponFighting(),
                asis=[
                    GreatWeaponMaster(weapon),
                    PolearmMaster(bonus_weapon) if use_pam else ASI(["str"]),
                    ASI(["str"]),
                    ASI(),
                    ASI(),
                    ASI(),
                    IrresistibleOffense("str"),
                ],
            )
        )
        
        # Initialize character
        super().__init__(
            name=self.name,
            level=level,
            stats=[17, 10, 10, 10, 10, 10],  # Str-focused build
            base_feats=feats,
        )


class ChampionFighter(Fighter):
    """
    Champion Fighter subclass.
    
    Focuses on improved critical hits and martial prowess.
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Champion Fighter.
        
        Args:
            level: Character level (3-20)
            **kwargs: Additional Fighter initialization arguments
        """
        self.name = "Champion Fighter"
        super().__init__(
            name=self.name,
            level=level,
            subclass_feats=champion_feats(level),
            **kwargs,
        )


class BattlemasterFighter(Fighter):
    """
    Battlemaster Fighter subclass (base, without specific maneuvers).
    
    Provides Combat Superiority dice pool.
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Battlemaster Fighter.
        
        Args:
            level: Character level (3-20)
            **kwargs: Additional Fighter initialization arguments
        """
        self.name = "Battlemaster Fighter"
        feats: List["sim.feat.Feat"] = []
        feats.extend(battlemaster_feats(level))
        super().__init__(name=self.name, level=level, subclass_feats=feats, **kwargs)


class TrippingFighter(Fighter):
    """
    Battlemaster Fighter specialized in Tripping Attack maneuver.
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Tripping Attack Battlemaster.
        
        Args:
            level: Character level (3-20)
            **kwargs: Additional Fighter initialization arguments
        """
        self.name = "Tripping Fighter"
        feats: List["sim.feat.Feat"] = []
        feats.append(TrippingAttack())
        feats.extend(battlemaster_feats(level))
        super().__init__(name=self.name, level=level, subclass_feats=feats, **kwargs)


class PrecisionFighter(Fighter):
    """
    Battlemaster Fighter specialized in Precision Attack maneuver.
    """
    
    def __init__(self, level: int, low: int = 8, **kwargs):
        """
        Initialize Precision Attack Battlemaster.
        
        Args:
            level: Character level (3-20)
            low: Minimum d20 roll to trigger precision (default 8)
            **kwargs: Additional Fighter initialization arguments
        """
        self.name = "Precision Fighter"
        feats: List[sim.feat.Feat] = []
        feats.append(PrecisionAttack(low=low))
        feats.extend(battlemaster_feats(level))
        super().__init__(name=self.name, level=level, subclass_feats=feats, **kwargs)


class PrecisionTrippingFighter(Fighter):
    """
    Battlemaster Fighter using both Precision and Tripping Attack maneuvers.
    """
    
    def __init__(self, level: int, low: int = 1, **kwargs):
        """
        Initialize combined Precision/Tripping Battlemaster.
        
        Args:
            level: Character level (3-20)
            low: Minimum d20 roll to trigger precision (default 1)
            **kwargs: Additional Fighter initialization arguments
        """
        self.name = "Precision/Tripping Fighter"
        feats: List["sim.feat.Feat"] = []
        feats.append(TrippingAttack())
        feats.append(PrecisionAttack(low=low))
        feats.extend(battlemaster_feats(level))
        super().__init__(name=self.name, level=level, subclass_feats=feats, **kwargs)


class TWFFighter(sim.character.Character):
    """
    Two-Weapon Fighting Fighter (Champion).
    
    Uses Vex and Nick weapon masteries for optimal dual-wielding.
    """
    
    def __init__(self, level: int, **kwargs) -> None:
        """
        Initialize Two-Weapon Fighting Fighter.
        
        Args:
            level: Character level (1-20)
            **kwargs: Additional character initialization arguments
        """
        self.name = "TWF Fighter"
        magic_weapon = get_magic_weapon(level)
        feats: List["sim.feat.Feat"] = []
        
        # Upgrade to Rapier at level 6 (Dual Wielder feat)
        if level >= 6:
            weapon: "sim.weapons.Weapon" = Rapier(magic_bonus=magic_weapon)
        else:
            weapon = Shortsword(magic_bonus=magic_weapon)
            
        nick_weapon = Scimitar(magic_bonus=magic_weapon)
        
        # Attack action with Nick bonus attack
        feats.append(DefaultFighterAction(level, weapon, nick_weapon=nick_weapon))
        
        # Origin Feat
        feats.append(SavageAttacker())
        
        # Two-Weapon Fighting progression
        feats.extend(
            fighter_feats(
                level,
                masteries=["Vex", "Nick"],
                fighting_style=TwoWeaponFighting(),
                asis=[
                    GreatWeaponMaster(weapon),  # Works with melee weapons
                    DualWielder("str", weapon),
                    ASI(["str"]),
                    ASI(),
                    ASI(),
                    ASI(),
                    IrresistibleOffense("str"),
                ],
            )
        )
        
        # Champion subclass
        feats.extend(champion_feats(level))
        
        # Initialize character
        super().__init__(
            name=self.name,
            level=level,
            stats=[17, 10, 10, 10, 10, 10],  # Str-focused
            base_feats=feats,
        )
