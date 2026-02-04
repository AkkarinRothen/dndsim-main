"""
Monk class implementation for D&D 5e combat simulator.

This module implements Monk class features including Martial Arts, Ki Points,
Flurry of Blows, Stunning Strike, and the Way of the Open Hand tradition.

FIXED ISSUES:
- Proper __init__ pattern with explicit name parameter
- Ki resource initialization in feat apply() methods
- Correct super().__init__() usage
- Clear martial arts die progression
"""

from typing import List, Optional

from util.util import get_magic_weapon, apply_asi_feats
from feats.epic_boons import IrresistibleOffense
from feats.origin import TavernBrawler
from feats import ASI, Grappler

import sim.core_feats
import sim.feat
import sim.character
import sim.target
import sim.weapons


# ============================================================================
# CONSTANTS & UTILITIES
# ============================================================================

def martial_arts_die(level: int) -> int:
    """
    Get the martial arts die size for a given Monk level.
    
    Args:
        level: Monk level (1-20)
        
    Returns:
        Die size (6, 8, 10, or 12)
    """
    if level >= 17:
        return 12
    elif level >= 11:
        return 10
    elif level >= 5:
        return 8
    else:
        return 6


# ============================================================================
# CORE MONK FEATURES
# ============================================================================

class MonkLevel(sim.core_feats.ClassLevels):
    """
    Represents Monk class levels.
    
    Monks are martial artists who channel ki energy.
    """
    
    def __init__(self, level: int):
        """
        Initialize Monk class levels.
        
        Args:
            level: Character level (1-20)
        """
        super().__init__(name="Monk", level=level)


class Ki(sim.feat.Feat):
    """
    Level 2 Monk feature: Ki.
    
    You gain a pool of Ki Points equal to your Monk level.
    Ki recharges on short rest.
    """
    
    def __init__(self, max_ki: int):
        """
        Initialize Ki pool.
        
        Args:
            max_ki: Maximum Ki points (usually equal to Monk level)
        """
        super().__init__()
        self.max_ki: int = max_ki

    def apply(self, character: "sim.character.Character") -> None:
        """
        Apply Ki pool to character.
        
        Args:
            character: The character to apply Ki to
        """
        super().apply(character)
        character.add_resource('Ki', max_uses=self.max_ki, short_rest=True)


class BodyAndMind(sim.feat.Feat):
    """
    Level 20 Monk feature: Body and Mind.
    
    Increases Dexterity and Wisdom maximum and current values by 4.
    Represents the pinnacle of monastic training.
    """
    
    def apply(self, character: "sim.character.Character") -> None:
        """
        Apply stat increases.
        
        Args:
            character: The character to enhance
        """
        super().apply(character)
        character.increase_stat_max("dex", 4)
        character.increase_stat_max("wis", 4)
        character.increase_stat("dex", 4)
        character.increase_stat("wis", 4)


class FlurryOfBlows(sim.feat.Feat):
    """
    Level 2 Monk feature: Flurry of Blows.
    
    Spend 1 Ki point to make two unarmed strikes as a bonus action.
    Gains a third attack at level 10.
    """
    
    def __init__(self, num_attacks: int, weapon: "sim.weapons.Weapon"):
        """
        Initialize Flurry of Blows.
        
        Args:
            num_attacks: Number of bonus attacks (2 or 3)
            weapon: Weapon to use for flurry attacks
        """
        super().__init__()
        self.num_attacks: int = num_attacks
        self.weapon: "sim.weapons.Weapon" = weapon

    def before_action(self, target: "sim.target.Target") -> None:
        """
        Trigger Flurry of Blows before main action if Ki available.
        
        Args:
            target: Combat target
        """
        if self.character.resources['Ki'].has() and self.character.use_bonus("FlurryOfBlows"):
            self.character.resources['Ki'].use(detail="Flurry of Blows", target=target)
            for _ in range(self.num_attacks):
                self.character.weapon_attack(target, self.weapon, tags=["flurry"])
        elif self.character.use_bonus("BonusAttack"):
            # Standard bonus unarmed strike if not using Flurry
            self.character.weapon_attack(target, self.weapon)


class StunningStrike(sim.feat.Feat):
    """
    Level 5 Monk feature: Stunning Strike.
    
    When you hit with a melee attack, spend 1 Ki to force a Constitution save.
    On failure, the target is stunned until the end of your next turn.
    """
    
    def __init__(self, level: int, avoid_on_grapple: bool = False):
        """
        Initialize Stunning Strike.
        
        Args:
            level: Monk level (for martial arts die)
            avoid_on_grapple: Don't use on grappled targets (optimization)
        """
        super().__init__()
        self.weapon_die: int = martial_arts_die(level)
        self.stuns: List[int] = []
        self.avoid_on_grapple: bool = avoid_on_grapple
        self.used: bool = False

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Reset usage and clear stun status.
        
        Args:
            target: Combat target
        """
        self.used = False
        target.stunned = False

    def attack_result(self, args) -> None:
        """
        Apply Stunning Strike on hit if conditions are met.
        
        Args:
            args: Attack result arguments
        """
        target = args.attack.target
        
        # Don't use if conditions aren't met
        if args.misses() or self.used or not self.character.resources['Ki'].has():
            return
        if target.grappled and self.avoid_on_grapple:
            return
        if target.stunned:
            return
        
        # Attempt to stun
        self.used = True
        self.character.resources['Ki'].use(detail="Stunning Strike", target=target)
        
        if not target.save("con", self.character.dc("wis")):
            target.stunned = True
        else:
            target.semistunned = True


# ============================================================================
# WAY OF THE OPEN HAND TRADITION
# ============================================================================

class OpenHandTechnique(sim.feat.Feat):
    """
    Way of the Open Hand Level 3 feature: Open Hand Technique.
    
    When you hit with a Flurry of Blows attack, you can impose one effect:
    - Knock target prone (if they fail a Dex save)
    - Push target 15 feet
    - Prevent reactions until end of your next turn
    
    For DPR purposes, we use the prone condition.
    """
    
    def attack_result(self, args) -> None:
        """
        Apply Open Hand Technique to Flurry attacks.
        
        Args:
            args: Attack result arguments
        """
        if args.hits() and args.attack.has_tag("flurry"):
            if not args.attack.target.save("dex", self.character.dc("wis")):
                args.attack.target.knock_prone()


# ============================================================================
# UNARMED STRIKE WEAPON
# ============================================================================

class Fists(sim.weapons.Weapon):
    """
    Monk unarmed strikes that scale with Martial Arts.
    
    Uses Dexterity or Strength, scales damage die with level.
    """
    
    def __init__(self, weapon_die: int, **kwargs):
        """
        Initialize unarmed strikes.
        
        Args:
            weapon_die: Size of martial arts die (6, 8, 10, or 12)
            **kwargs: Additional weapon parameters (like magic_bonus)
        """
        super().__init__(
            name="Fists",
            num_dice=1,
            die=weapon_die,
            tags=["finesse"],
            **kwargs,
        )


# ============================================================================
# FEAT BUILDERS
# ============================================================================

def monk_feats(
    level: int,
    asis: Optional[List["sim.feat.Feat"]] = None
) -> List["sim.feat.Feat"]:
    """
    Build the standard Monk feat list for a given level.
    
    Args:
        level: Character level (1-20)
        asis: ASI/feat choices at appropriate levels
        
    Returns:
        List of Monk class feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 1: Class basics
    if level >= 1:
        feats.append(MonkLevel(level))
    
    # Level 1: Unarmored Defense (not relevant for DPR)
    
    # Level 2: Ki
    if level >= 2:
        feats.append(Ki(level))
    
    # Level 2: Uncanny Metabolism (TODO)
    
    # Level 3: Deflect Attacks (defensive, not relevant)
    # Level 4: Slow Fall (utility, not relevant)
    
    # Level 5: Stunning Strike
    if level >= 5:
        feats.append(StunningStrike(level, avoid_on_grapple=True))
    
    # Level 6: Empowered Strikes (bypasses resistance, not relevant for sim)
    # Level 7: Evasion (defensive, not relevant)
    # Level 9: Acrobatic Movement (mobility, not relevant)
    # Level 10: Self-Restoration (healing, not relevant)
    # Level 13: Deflect Energy (defensive, not relevant)
    # Level 14: Disciplined Survivor (saves, not relevant)
    
    # Level 15: Perfect Focus (TODO: implementation)
    
    # Level 18: Superior Defense (defensive, not relevant)
    
    # Level 20: Body and Mind
    if level >= 20:
        feats.append(BodyAndMind())
    
    # Apply ASIs/Feats
    apply_asi_feats(level=level, feats=feats, asis=asis)
    
    return feats


def open_hand_monk_feats(level: int) -> List["sim.feat.Feat"]:
    """
    Build Way of the Open Hand tradition feat list.
    
    Args:
        level: Character level (3-20)
        
    Returns:
        List of Open Hand tradition feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 3: Open Hand Technique
    if level >= 3:
        feats.append(OpenHandTechnique())
    
    # Level 6: Wholeness of Body (healing, not relevant)
    # Level 11: Fleet Step (mobility, not relevant)
    # Level 17: Quivering Palm (TODO: complex implementation)
    
    return feats


# ============================================================================
# COMBAT ACTION
# ============================================================================

class DefaultMonkAction(sim.feat.Feat):
    """
    Standard Monk combat action.
    
    - Makes 1 attack (2 at level 5+)
    - Uses Flurry of Blows if Ki available
    - Falls back to bonus unarmed strike otherwise
    """
    
    def __init__(self, level: int, weapon: "sim.weapons.Weapon"):
        """
        Initialize Monk action.
        
        Args:
            level: Monk level
            weapon: Unarmed strike weapon
        """
        super().__init__()
        self.level: int = level
        self.weapon: "sim.weapons.Weapon" = weapon

    def action(self, target: "sim.target.Target") -> None:
        """
        Execute Monk combat action.
        
        Args:
            target: Combat target
        """
        # Main attacks
        num_attacks = 2 if self.character.has_class_level("Monk", 5) else 1
        for _ in range(num_attacks):
            self.character.weapon_attack(target, self.weapon, tags=["main_action"])
        
        # Flurry of Blows (bonus action)
        if (
            self.character.has_class_level("Monk", 2)
            and self.character.resources['Ki'].has()
            and self.character.use_bonus("FlurryOfBlows")
        ):
            self.character.resources['Ki'].use(detail="Flurry of Blows", target=target)
            num_flurry = 3 if self.character.has_class_level("Monk", 10) else 2
            for _ in range(num_flurry):
                self.character.weapon_attack(target, self.weapon, tags=["flurry"])
        
        # Fallback bonus attack
        elif self.character.use_bonus("BonusAttack"):
            self.character.weapon_attack(target, self.weapon)


# ============================================================================
# CHARACTER CLASS
# ============================================================================

class OpenHandMonk(sim.character.Character):
    """
    Way of the Open Hand Monk.
    
    A martial artist who uses Ki to enhance attacks and control the battlefield.
    
    The Open Hand Monk excels at:
    - High number of attacks (Extra Attack + Flurry of Blows)
    - Stunning Strike for control
    - Open Hand Technique for knocking enemies prone
    - Scaling unarmed damage via Martial Arts
    
    Combat Strategy:
    - Uses Flurry of Blows when Ki available
    - Attempts Stunning Strike on important hits
    - Knocks enemies prone with Open Hand Technique
    - Grapples with Tavern Brawler for advantage
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Way of the Open Hand Monk.
        
        Args:
            level: Character level (1-20)
            **kwargs: Additional character initialization arguments
        """
        # Calculate martial arts die and weapon
        magic_weapon = get_magic_weapon(level)
        weapon_die = martial_arts_die(level)
        fists = Fists(weapon_die, magic_bonus=magic_weapon)
        
        # Build feat list
        feats: List["sim.feat.Feat"] = []
        
        # Origin feat
        feats.append(TavernBrawler())
        
        # Monk class progression
        feats.extend(
            monk_feats(
                level=level,
                asis=[
                    Grappler("dex"),        # Synergizes with Tavern Brawler
                    ASI(["dex"]),           # Boost primary stat
                    ASI(["wis"]),           # Boost Ki save DC
                    ASI(["wis"]),           # More save DC
                    IrresistibleOffense("dex"),  # Epic boon at high levels
                ],
            )
        )
        
        # Open Hand tradition
        feats.extend(open_hand_monk_feats(level))
        
        # Combat action
        feats.append(DefaultMonkAction(level, fists))
        
        # Initialize character
        # Stats: Dexterity for attacks/AC, Wisdom for Ki DC/features
        super().__init__(
            name="Open Hand Monk",  # ✅ Explicit name
            level=level,
            stats=[10, 17, 10, 10, 16, 10],  # Dex/Wis focused
            base_feats=feats,
        )
