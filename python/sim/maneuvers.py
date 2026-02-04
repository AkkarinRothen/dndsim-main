"""
Battle Master maneuvers system for fighters.

This module implements the superiority dice system used by Battle Master
fighters in D&D 5e.
"""
from typing import TYPE_CHECKING

from util.util import roll_dice

if TYPE_CHECKING:
    import sim.target


class Maneuvers:
    """
    Tracks superiority dice for Battle Master maneuvers.
    
    Superiority dice are expended to fuel combat maneuvers and recharge
    on short rest. The Relentless feature allows using one d8 when out
    of dice once per turn.
    
    Attributes:
        max_dice: Maximum number of superiority dice
        die: Die size (d6, d8, d10, or d12)
        dice: Current number of dice remaining
        relentless: Whether Relentless feature is active
        used_relentless: Whether Relentless was used this turn
        
    Examples:
        >>> # Battle Master level 3
        >>> maneuvers = Maneuvers()
        >>> maneuvers.max_dice = 4
        >>> maneuvers.die = 8
        >>> maneuvers.short_rest()
        >>> 
        >>> # Use a maneuver
        >>> if maneuvers.has_die():
        ...     damage = maneuvers.roll()
        ...     print(f"Added {damage} damage!")
    """
    
    def __init__(self, character: "sim.character.Character") -> None:
        """
        Initialize maneuvers system.
        
        Args:
            character: The character that owns this maneuvers system.
            
        Starts with no dice. Call increase_max() or set max_dice
        directly when gaining Battle Master levels.
        """
        self.character = character
        self.max_dice = 0
        self.die = 0
        self.dice = 0
        self.relentless = False
        self.used_relentless = False

    def increase_max(self, amount: int = 1) -> None:
        """
        Increase maximum number of superiority dice.
        
        Args:
            amount: Number of dice to add (default 1)
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot increase max by negative amount: {amount}")
        
        self.max_dice += amount

    def set_die_size(self, die: int) -> None:
        """
        Set superiority die size.
        
        Args:
            die: Die size (6, 8, 10, or 12)
            
        Raises:
            ValueError: If die size is invalid
        """
        if die not in [6, 8, 10, 12]:
            raise ValueError(
                f"Invalid superiority die size: d{die}. "
                "Must be d6, d8, d10, or d12"
            )
        
        self.die = die

    def enable_relentless(self) -> None:
        """
        Enable Relentless feature (Battle Master level 15).
        
        Allows using a d8 when out of dice, once per turn.
        """
        self.relentless = True

    def short_rest(self) -> None:
        """
        Recharge all superiority dice on short rest.
        """
        self.dice = self.max_dice

    def long_rest(self) -> None:
        """
        Recharge all superiority dice on long rest.
        """
        self.short_rest()

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Reset Relentless at start of turn.
        
        Args:
            target: Current combat target (unused)
        """
        self.used_relentless = False

    def has_die(self) -> bool:
        """
        Check if a superiority die is available.
        
        Includes Relentless if applicable.
        
        Returns:
            True if can use a die
        """
        return self.dice > 0 or (self.relentless and not self.used_relentless)

    def use(self) -> int:
        """
        Expend a superiority die and get its size.
        
        Uses a normal die if available, otherwise uses Relentless
        if applicable.
        
        Returns:
            Die size to roll (0 if no dice available)
        """
        # Use normal die if available
        if self.dice > 0:
            self.dice -= 1
            self.character.record_resource_use("maneuvers", "Superiority Die", 1) # Record maneuver usage
            return self.die
        
        # Use Relentless if available
        if self.relentless and not self.used_relentless:
            self.used_relentless = True
            self.character.record_resource_use("maneuvers", "Relentless (Superiority Die)", 1) # Record Relentless usage
            return 8  # Relentless always uses d8
        
        # No dice available
        return 0

    def roll(self) -> int:
        """
        Expend a superiority die and roll it.
        
        Returns:
            Rolled value (0 if no dice available)
            
        Example:
            >>> maneuvers.dice = 3
            >>> damage = maneuvers.roll()  # Rolls 1d8 (or whatever die size)
            >>> print(f"Maneuver damage: {damage}")
        """
        die_size = self.use()
        
        if die_size > 0:
            return roll_dice(1, die_size)
        
        return 0

    def peek(self) -> int:
        """
        Check die size without using it.
        
        Returns:
            Die size that would be used (0 if none available)
        """
        if self.dice > 0:
            return self.die
        
        if self.relentless and not self.used_relentless:
            return 8
        
        return 0

    def remaining(self) -> int:
        """
        Get number of dice remaining.
        
        Returns:
            Number of superiority dice left
        """
        return self.dice

    def is_empty(self) -> bool:
        """
        Check if out of superiority dice.
        
        Does not account for Relentless.
        
        Returns:
            True if no normal dice remaining
        """
        return self.dice == 0

    def __str__(self) -> str:
        """String representation showing dice."""
        relentless_str = " (+Relentless)" if self.relentless else ""
        return f"Superiority Dice: {self.dice}/{self.max_dice} d{self.die}{relentless_str}"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Maneuvers(dice={self.dice}/{self.max_dice}, "
            f"die=d{self.die}, relentless={self.relentless})"
        )

    def __bool__(self) -> bool:
        """
        Allow maneuvers to be used in boolean context.
        
        Returns:
            True if dice are available
            
        Example:
            >>> if character.maneuvers:
            ...     damage = character.maneuvers.roll()
        """
        return self.has_die()
