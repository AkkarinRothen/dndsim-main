"""
Event argument classes for combat system.

This module defines data classes that carry information about combat events
like attacks, damage rolls, and saving throws.
"""
from typing import List, Optional, TypeAlias, Callable, Any, TYPE_CHECKING
import random

from util.log import log
import util.taggable

if TYPE_CHECKING:
    import sim.target
    import sim.weapons
    import sim.spells
    import sim.character
    import sim.attack


class AttackArgs(util.taggable.Taggable):
    """
    Arguments for an attack action.
    
    Contains all information about an attack: target, weapon/spell,
    and any special tags.
    
    Attributes:
        target: Creature being attacked
        attack: Attack object (WeaponAttack or SpellAttack)
        weapon: Weapon being used (if weapon attack)
        spell: Spell being cast (if spell attack)
    """
    
    def __init__(
        self,
        target: "sim.target.Target",
        attack: "sim.attack.Attack",
        weapon: Optional["sim.weapons.Weapon"] = None,
        spell: Optional["sim.spells.Spell"] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Initialize attack arguments.
        
        Args:
            target: Target of the attack
            attack: Attack being made
            weapon: Weapon if weapon attack
            spell: Spell if spell attack
            tags: Optional attack tags (e.g., "bonus_action", "offhand")
        """
        super().__init__()
        
        self.target = target
        self.attack = attack
        self.weapon = weapon
        self.spell = spell
        
        if tags:
            self.add_tags(tags)


class AttackRollArgs:
    """
    Arguments for an attack roll.
    
    Tracks the d20 rolls, advantage/disadvantage, and modifiers that
    determine if an attack hits.
    
    Attributes:
        attack: Attack being rolled for
        to_hit: Base attack bonus
        adv: Whether roll has advantage
        disadv: Whether roll has disadvantage
        roll1: First d20 roll
        roll2: Second d20 roll (for advantage/disadvantage)
        situational_bonus: Additional bonus to attack roll
        min_crit: Override for critical hit threshold (default 20)
    """
    
    def __init__(self, attack: AttackArgs, to_hit: int):
        """
        Initialize attack roll.
        
        Args:
            attack: Attack being rolled for
            to_hit: Base attack bonus
        """
        self.attack = attack
        self.to_hit = to_hit
        self.adv = False
        self.disadv = False
        self.roll1 = random.randint(1, 20)
        self.roll2 = random.randint(1, 20)
        self.situational_bonus = 0
        self.min_crit: Optional[int] = None

    def reroll(self) -> None:
        """
        Reroll both d20s.
        
        Used by features like Lucky or Elven Accuracy.
        """
        self.roll1 = random.randint(1, 20)
        self.roll2 = random.randint(1, 20)

    def roll(self) -> int:
        """
        Get the final d20 result after advantage/disadvantage.
        
        Returns:
            The d20 roll to use for the attack
        """
        # Advantage and disadvantage cancel out
        if self.adv and self.disadv:
            log.output(lambda: f"Roll (ADV+DIS cancel): {self.roll1}")
            return self.roll1
        
        # Advantage: take higher roll
        if self.adv:
            result = max(self.roll1, self.roll2)
            log.output(lambda: f"Roll (ADV): {self.roll1}, {self.roll2} = {result}")
            return result
        
        # Disadvantage: take lower roll
        if self.disadv:
            result = min(self.roll1, self.roll2)
            log.output(lambda: f"Roll (DIS): {self.roll1}, {self.roll2} = {result}")
            return result
        
        # Normal roll
        log.output(lambda: f"Roll: {self.roll1}")
        return self.roll1

    def hits(self) -> bool:
        """
        Check if attack hits target AC.
        
        Returns:
            True if roll + modifiers >= target AC
        """
        total = self.roll() + self.to_hit + self.situational_bonus
        return total >= self.attack.target.ac

    def total(self) -> int:
        """
        Calculate total attack roll.
        
        Returns:
            d20 + to_hit + situational bonuses
        """
        return self.roll() + self.to_hit + self.situational_bonus


class AttackResultArgs:
    """
    Results of an attack roll.
    
    Contains information about whether the attack hit, if it was a crit,
    and all damage rolls that should be applied.
    
    Attributes:
        attack: Attack that was made
        hit: Whether attack hit
        crit: Whether attack was a critical hit
        roll: The actual d20 roll result
        damage_rolls: List of damage to apply
        dmg_multiplier: Multiplier for all damage (e.g., vulnerability)
    """
    
    def __init__(
        self,
        attack: AttackArgs,
        hit: bool,
        crit: bool,
        roll: int,
    ):
        """
        Initialize attack result.
        
        Args:
            attack: Attack that was rolled
            hit: Whether attack succeeded
            crit: Whether it was a critical hit
            roll: The d20 roll result
        """
        self.attack = attack
        self.hit = hit
        self.crit = crit
        self.roll = roll
        self.damage_rolls: List["sim.attack.DamageRoll"] = []
        self.dmg_multiplier = 1.0

    def add_damage(
        self,
        source: str,
        dice: Optional[List[int]] = None,
        damage: int = 0,
        damage_type: str = "physical",
    ) -> None:
        """
        Add a damage roll to this attack.
        
        Args:
            source: Source of damage (weapon name, spell name, etc.)
            dice: Dice to roll (e.g., [6, 6] for 2d6)
            damage: Flat damage to add
            damage_type: Type of damage (slashing, fire, etc.)
        """
        import sim.attack
        
        dice = dice or []
        self.damage_rolls.append(
            sim.attack.DamageRoll(
                source=source,
                dice=dice,
                flat_dmg=damage,
                damage_type=damage_type
            )
        )

    def hits(self) -> bool:
        """Check if attack hit."""
        return self.hit

    def misses(self) -> bool:
        """Check if attack missed."""
        return not self.hit

    def is_crit(self) -> bool:
        """Check if attack was a critical hit."""
        return self.crit

    def total_damage(self) -> int:
        """
        Calculate total damage from all rolls.
        
        Returns:
            Sum of all damage rolls (before multiplier)
        """
        return sum(dmg.total() for dmg in self.damage_rolls)


# Type alias for attack result callbacks
AttackResultCallback: TypeAlias = Callable[
    [AttackResultArgs, "sim.character.Character"], Any
]


class EnemySavingThrowArgs:
    """
    Arguments for an enemy saving throw.
    
    Currently a placeholder for future expansion.
    """
    
    def __init__(self, ability: str, dc: int) -> None:
        """
        Initialize saving throw args.
        
        Args:
            ability: Ability being used for save
            dc: Difficulty Class to beat
        """
        self.ability = ability
        self.dc = dc


class CastSpellArgs:
    """
    Arguments for casting a spell.
    
    Contains information about the spell being cast and any modifiers.
    
    Attributes:
        spell: Spell being cast
        upcast_level: Level the spell is being cast at (if upcasting)
    """
    
    def __init__(self, spell: "sim.spells.Spell") -> None:
        """
        Initialize spell casting args.
        
        Args:
            spell: Spell being cast
        """
        self.spell = spell
        self.upcast_level: Optional[int] = None


class DamageRollArgs:
    """
    Arguments for a damage roll.
    
    Contains information about damage being dealt, allowing feats and
    features to modify damage before it's applied.
    
    Attributes:
        target: Creature taking damage
        damage: DamageRoll with dice and modifiers
        attack: Attack that caused damage (if applicable)
        spell: Spell that caused damage (if applicable)
    """
    
    def __init__(
        self,
        target: "sim.target.Target",
        damage: "sim.attack.DamageRoll",
        attack: Optional[AttackArgs] = None,
        spell: Optional["sim.spells.Spell"] = None,
    ) -> None:
        """
        Initialize damage roll args.
        
        Args:
            target: Target taking damage
            damage: Damage roll
            attack: Attack that caused damage
            spell: Spell that caused damage
        """
        self.target = target
        self.damage = damage
        self.attack = attack
        self.spell = spell

    def is_attack_damage(self) -> bool:
        """Check if damage is from an attack."""
        return self.attack is not None

    def is_spell_damage(self) -> bool:
        """Check if damage is from a spell."""
        return self.spell is not None

    def is_weapon_damage(self) -> bool:
        """Check if damage is from a weapon attack."""
        return self.attack is not None and self.attack.weapon is not None


class BeginTurnArgs:
    """
    Arguments for beginning a turn.
    
    Attributes:
        target: Current combat target
        turn_number: Which turn this is (if tracked)
    """
    
    def __init__(
        self,
        target: "sim.target.Target",
        turn_number: Optional[int] = None
    ):
        """
        Initialize begin turn args.
        
        Args:
            target: Combat target
            turn_number: Turn number in combat
        """
        self.target = target
        self.turn_number = turn_number


class EndTurnArgs:
    """
    Arguments for ending a turn.
    
    Attributes:
        target: Current combat target
    """
    
    def __init__(self, target: "sim.target.Target"):
        """
        Initialize end turn args.
        
        Args:
            target: Combat target
        """
        self.target = target
