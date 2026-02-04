"""
Resource management system for character abilities.

This module implements the Resource class for tracking limited-use abilities
like Ki points, Channel Divinity, Sorcery Points, etc.
"""
from typing import TYPE_CHECKING, Optional, Any
import math

import sim.event_loop
from util.log import log

if TYPE_CHECKING:
    import sim.character
    import sim.resource_tracker # Import the new tracker module


def pact_spell_slots(level: int) -> list[int]:
    """
    Calculate Warlock Pact Magic spell slots.
    
    Warlocks get a different spell slot progression that gives them
    fewer but higher-level slots that recharge on short rest.
    
    Args:
        level: Warlock level (1-20)
        
    Returns:
        List of slot levels (e.g., [5, 5, 5, 5] for 4x 5th-level slots)
        
    Examples:
        >>> pact_spell_slots(1)  # Level 1 warlock
        [1]
        >>> pact_spell_slots(5)  # Level 5 warlock
        [3, 3]
        >>> pact_spell_slots(17)  # Level 17 warlock
        [5, 5, 5, 5]
    """
    if level < 1:
        return []
    
    # Determine slot level
    if level >= 9:
        slot_level = 5
    elif level >= 7:
        slot_level = 4
    elif level >= 5:
        slot_level = 3
    elif level >= 3:
        slot_level = 2
    else:
        slot_level = 1
    
    # Determine number of slots
    if level >= 17:
        num_slots = 4
    elif level >= 11:
        num_slots = 3
    elif level >= 2:
        num_slots = 2
    else:
        num_slots = 1
    
    return [slot_level] * num_slots


class Resource(sim.event_loop.Listener):
    """
    Tracks a limited-use resource that recharges on rest.
    
    Resources can recharge on short rest or long rest. They have a maximum
    number of uses and track current uses remaining.
    
    Attributes:
        name: Display name for the resource
        num: Current number of uses remaining
        max: Maximum number of uses
        reset_on_short_rest: Whether resource recharges on short rest
        
    Examples:
        >>> # Ki points recharge on short rest
        >>> ki = Resource(character, "Ki", short_rest=True)
        >>> ki.increase_max(5)
        >>> ki.reset()  # Now has 5 ki points
        >>> 
        >>> # Channel Divinity recharges on short rest
        >>> channel = Resource(character, "Channel Divinity", short_rest=True)
        >>> channel.increase_max(2)
    """
    character: "sim.character.Character"
    name: str
    num: int
    max: int
    reset_on_short_rest: bool
    log: list[str]

    def __init__(
        self,
        character: "sim.character.Character",
        name: str,
        short_rest: bool = False
    ):
        self.character = character # Store reference to character for logging
        """
        Initialize a resource.
        
        Args:
            character: Character that owns this resource
            name: Display name for logging
            short_rest: If True, resource recharges on short rest;
                       otherwise only on long rest
        """
        self.name = name
        self.num = 0
        self.max = 0
        self.reset_on_short_rest = short_rest
        self.log = []
        
        # Register for rest events
        character.events.add(self, ["short_rest", "long_rest"])

    def increase_max(self, amount: int) -> None:
        """
        Increase the maximum number of uses.
        
        Args:
            amount: Amount to increase maximum by
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot increase max by negative amount: {amount}")
        
        self.max += amount

    def decrease_max(self, amount: int) -> None:
        """
        Decrease the maximum number of uses.
        
        Current uses are capped at new maximum.
        
        Args:
            amount: Amount to decrease maximum by
            
        Raises:
            ValueError: If amount is negative or would make max negative
        """
        if amount < 0:
            raise ValueError(f"Cannot decrease max by negative amount: {amount}")
        
        if self.max - amount < 0:
            raise ValueError(
                f"Cannot decrease max by {amount}: would result in negative max"
            )
        
        self.max -= amount
        
        # Cap current uses at new-maximum
        if self.num > self.max:
            self.num = self.max

    def short_rest(self) -> None:
        """
        Handle short rest.
        
        Resets resource if it recharges on short rest.
        """
        if self.reset_on_short_rest:
            self.reset()

    def long_rest(self) -> None:
        """
        Handle long rest.
        
        Always resets resource.
        """
        self.reset()

    def reset(self) -> None:
        """
        Reset resource to maximum uses.
        """
        self.num = self.max
        self.log.clear()
        log.output(lambda: f"{self.name} reset to {self.max}")

    def gain(self, amount: int = 1, detail: Optional[str] = None) -> None:
        """
        Gain uses of the resource, up to its maximum.
        
        Args:
            amount: Number of uses to gain (default 1)
            detail: Optional string describing the gain
        """
        if amount < 0:
            raise ValueError(f"Cannot gain negative amount: {amount}")
        
        self.num = min(self.max, self.num + amount)
        log.output(lambda: f"{self.name} gained {amount} uses, now {self.num}/{self.max}")
        if detail:
            self.log.append(f"Gained: {detail}")

    def use(self, amount: int = 1, detail: Optional[str] = None, target: Optional["sim.target.Target"] = None) -> bool:
        """
        Attempt to use resource.
        
        Args:
            amount: Number of uses to consume (default 1)
            detail: Optional string describing the use
            target: Optional target of the action that consumes the resource
            
        Returns:
            True if resource was available and used, False otherwise
        """
        if amount < 0:
            raise ValueError(f"Cannot use negative amount: {amount}")
        
        if self.num >= amount:
            log.record(f"Resource ({self.name})", amount)
            self.num -= amount
            if detail:
                log_detail = f"Round {self.character.current_round}: {detail}"
                if target:
                    log_detail += f" against {target.name}"
                self.log.append(log_detail)
            return True
        
        return False

    def has(self, amount: int = 1) -> bool:
        """
        Check if resource has at least the specified amount available.
        
        Args:
            amount: Minimum number of uses needed (default 1)
            
        Returns:
            True if resource has enough uses remaining
        """
        return self.num >= amount

    def is_empty(self) -> bool:
        """
        Check if resource is completely depleted.
        
        Returns:
            True if no uses remaining
        """
        return self.num == 0

    def is_full(self) -> bool:
        """
        Check if resource is at maximum uses.
        
        Returns:
            True if at maximum
        """
        return self.num == self.max

    def remaining(self) -> int:
        """
        Get number of uses remaining.
        
        Returns:
            Current uses remaining
        """
        return self.num
    
    @property
    def used(self) -> int:
        """Get number of uses consumed."""
        return self.max - self.num

    def get_usage_summary(self) -> dict[str, Any]:
        """
        Get a summary of resource usage.
        
        Returns:
            A dictionary with usage details, compatible with the tracker.
        """
        if self.used == 0:
            return {}
            
        percentage = (self.used / self.max) * 100 if self.max > 0 else 0.0
        
        return {
            'used': self.used,
            'max': self.max,
            'remaining': self.remaining(),
            'percentage': f"{percentage:.1f}%",
            'details': self.log if self.log else None
        }

    def __str__(self) -> str:
        """String representation showing uses."""
        return f"{self.name}: {self.num}/{self.max}"

    def __repr__(self) -> str:
        """Detailed string representation."""
        rest_type = "short" if self.reset_on_short_rest else "long"
        return (
            f"Resource(name='{self.name}', {self.num}/{self.max}, "
            f"resets_on={rest_type}_rest)"
        )

    def __bool__(self) -> bool:
        """
        Allow resource to be used in boolean context.
        
        Returns:
            True if resource has uses remaining
            
        Example:
            >>> if character.ki:
            ...     character.ki.use()
        """
        return self.has()


class WarlockPactSlots(Resource):
    """
    Manages Warlock Pact Magic spell slots as a resource.
    """
    def __init__(self, character: "sim.character.Character", warlock_level: int):
        super().__init__(character, "Pact Slots", short_rest=True)
        self.warlock_level = warlock_level
        self.slot_level: int = 0
        self.num_slots: int = 0
        self._update_slots()

    def _update_slots(self) -> None:
        """Calculates current slot level and number of slots based on Warlock level."""
        pact_slots_info = pact_spell_slots(self.warlock_level)
        if pact_slots_info:
            self.slot_level = pact_slots_info[0]
            self.num_slots = len(pact_slots_info)
        else:
            self.slot_level = 0
            self.num_slots = 0
        self.max = self.num_slots
        self.num = self.num_slots # Reset current uses to max when updating

    def increase_max(self, amount: int) -> None:
        """
        Warlock Pact Slots increase max dynamically with level, not by arbitrary amount.
        This method will update the Warlock level and recalculate slots.
        """
        self.warlock_level += amount # Assuming amount is level increase
        self._update_slots()
        log.output(lambda: f"Pact Slots max updated to {self.num_slots}x{self.slot_level}th level slots due to Warlock level increase.")

    def get_slot_level(self) -> int:
        """Returns the level of the Pact Slots."""
        return self.slot_level

    def use(self, amount: int = 1, detail: Optional[str] = None, target: Optional["sim.target.Target"] = None) -> bool:
        """
        Attempt to use a Pact Slot.
        
        Args:
            amount: Number of slots to consume (default 1)
            detail: Optional string describing the use
            
        Returns:
            True if slot was available and used, False otherwise
        """
        if self.num >= amount:
            log.record(f"{self.name} ({self.slot_level}th)", amount)
            self.num -= amount
            if detail:
                log_detail = f"Round {self.character.current_round}: {detail} (Level {self.slot_level})"
                if target:
                    log_detail += f" against {target.name}"
                self.log.append(log_detail)
            return True
        return False
        
    def has(self, amount: int = 1) -> bool:
        """
        Check if Pact Slots are available.
        """
        return self.num >= amount

    def __str__(self) -> str:
        """String representation showing uses."""
        return f"{self.name}: {self.num}/{self.num_slots}x{self.slot_level}th"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"WarlockPactSlots(level={self.warlock_level}, "
            f"slots={self.num}/{self.num_slots}x{self.slot_level}th)"
        )

