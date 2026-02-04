"""
Combat attack system for D&D 5e simulation.

This module handles damage rolls, attack types (weapon/spell), and attack resolution.
"""
from typing import Optional, Protocol, Self, Callable, Any, TYPE_CHECKING
from dataclasses import dataclass, field

from util.util import roll_dice
from sim.events import AttackResultArgs

if TYPE_CHECKING:
    import sim.spells
    import sim.weapons


@dataclass
class DamageRoll:
    """
    Represents a damage roll with dice and flat modifiers.
    
    Attributes:
        source: Name of the damage source (weapon, spell, etc.)
        dice: List of die sizes to roll (e.g., [6, 6] for 2d6)
        flat_dmg: Flat damage modifier to add
        damage_type: Type of damage (physical, fire, cold, etc.)
        rolls: Actual dice roll results
    """
    source: str = "Unknown"
    dice: list[int] = field(default_factory=list)
    flat_dmg: int = 0
    damage_type: str = "physical"
    rolls: list[int] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """Initialize dice rolls after dataclass creation."""
        if not self.rolls:
            self.rolls = [roll_dice(1, die) for die in self.dice]
    
    @classmethod
    def from_dice_notation(
        cls,
        source: str,
        num_dice: int,
        die: int,
        flat_dmg: int = 0,
        damage_type: str = "physical",
    ) -> Self:
        """
        Create a DamageRoll from standard dice notation.
        
        Args:
            source: Name of the damage source
            num_dice: Number of dice to roll
            die: Die size (e.g., 6 for d6)
            flat_dmg: Flat damage modifier
            damage_type: Type of damage
            
        Returns:
            New DamageRoll instance
        """
        dice = [die] * num_dice
        return cls(
            source=source,
            dice=dice,
            flat_dmg=flat_dmg,
            damage_type=damage_type,
        )

    def total(self) -> int:
        """Calculate total damage including flat modifier."""
        return self.flat_dmg + sum(self.rolls)

    def reroll(self) -> None:
        """Reroll all dice (e.g., for reroll mechanics)."""
        self.rolls = [roll_dice(1, die) for die in self.dice]
    
    def double_dice(self) -> None:
        """Double the number of dice (for critical hits)."""
        self.dice = self.dice * 2
        self.rolls = [roll_dice(1, die) for die in self.dice]


class CharacterProtocol(Protocol):
    """Protocol defining the Character interface needed for attacks."""
    
    def mod(self, stat: str) -> int:
        """Get ability modifier for a stat."""
        ...
    
    @property
    def spells(self) -> Any:
        """Access to spellcasting system."""
        ...


class Attack:
    """
    Base class for all attack types.
    
    Subclasses must implement to_hit(), attack_result(), and is_ranged().
    """
    
    def __init__(self, name: str) -> None:
        """
        Initialize attack.
        
        Args:
            name: Display name for the attack
        """
        self.name = name

    def to_hit(self, character: CharacterProtocol) -> int:
        """
        Calculate attack bonus.
        
        Args:
            character: The attacking character
            
        Returns:
            Attack bonus to add to d20 roll
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_hit()"
        )

    def attack_result(self, args: AttackResultArgs, character: CharacterProtocol) -> None:
        """
        Handle attack result and apply damage.
        
        Args:
            args: AttackResultArgs containing hit/crit information
            character: The attacking character
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement attack_result()"
        )

    def min_crit(self) -> int:
        """
        Get minimum d20 roll needed for critical hit.
        
        Returns:
            Minimum roll for crit (default 20)
        """
        return 20

    def is_ranged(self) -> bool:
        """
        Check if this is a ranged attack.
        
        Returns:
            True if ranged, False if melee
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement is_ranged()"
        )


class SpellAttack(Attack):
    """
    Spell attack requiring an attack roll.
    
    Attributes:
        spell: The spell being cast
        damage: Optional damage roll for the spell
        callback: Optional callback for additional effects
        ranged: Whether this is a ranged spell attack
    """
    
    def __init__(
        self,
        spell: "sim.spells.Spell",
        damage: Optional[DamageRoll] = None,
        callback: Optional[Callable[[AttackResultArgs, "sim.character.Character"], Any]] = None,
        is_ranged: bool = False,
    ) -> None:
        """
        Initialize spell attack.
        
        Args:
            spell: Spell object being cast
            damage: Damage roll (if applicable)
            callback: Function to call with attack result
            is_ranged: Whether this is a ranged spell attack
        """
        super().__init__(name=spell.name)
        self.spell = spell
        self.callback = callback
        self.ranged = is_ranged
        self.damage = damage

    def to_hit(self, character: CharacterProtocol) -> int:
        """Get spell attack bonus from character's spellcasting."""
        return character.spells.to_hit()

    def attack_result(self, args: AttackResultArgs, character: CharacterProtocol) -> None:
        """
        Apply spell attack damage and effects.
        
        Doubles dice on critical hit and applies any callbacks.
        """
        if args.hits() and self.damage:
            dice = 2 * self.damage.dice if args.crit else self.damage.dice
            args.add_damage(
                self.spell.name,
                dice=dice,
                damage=self.damage.flat_dmg,
                damage_type=getattr(self.spell, 'damage_type', 'force')
            )
        
        if self.callback:
            self.callback(args, character)

    def is_ranged(self) -> bool:
        """Return whether this spell attack is ranged."""
        return self.ranged


class WeaponAttack(Attack):
    """
    Physical weapon attack.
    
    Delegates most behavior to the Weapon object.
    """
    
    def __init__(self, weapon: "sim.weapons.Weapon") -> None:
        """
        Initialize weapon attack.
        
        Args:
            weapon: Weapon object being used
        """
        super().__init__(weapon.name)
        self.weapon = weapon

    def to_hit(self, character: CharacterProtocol) -> int:
        """Get weapon attack bonus."""
        return self.weapon.to_hit(character)

    def attack_result(self, args: AttackResultArgs, character: CharacterProtocol) -> None:
        """Apply weapon attack result."""
        self.weapon.attack_result(args, character)

    def min_crit(self) -> int:
        """Get minimum crit range from weapon."""
        return self.weapon.min_crit()

    def is_ranged(self) -> bool:
        """Check if weapon has ranged tag."""
        return self.weapon.has_tag("ranged")
