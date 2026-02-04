"""
Event system for character abilities and combat mechanics.

This module implements a simple event emitter/listener pattern that allows
feats, spells, and other systems to react to game events like attacks,
damage, turns, and rests.
"""
from typing import Dict, List, Union, Optional, Callable, Any


class Listener:
    """
    Base class for objects that can listen to events.
    
    Listeners should implement methods matching event names
    (e.g., 'attack_roll', 'damage_roll') to respond to events.
    """
    pass


class EventLoop:
    """
    Event dispatcher for game events.
    
    Manages registration of listeners and dispatching of events to
    appropriate handlers. Events are dispatched synchronously in the
    order listeners were registered.
    
    Attributes:
        listeners: Dictionary mapping event names to lists of listeners
        
    Examples:
        >>> loop = EventLoop()
        >>> 
        >>> class MyListener(Listener):
        ...     def attack_roll(self, args):
        ...         print("Attack rolled!")
        >>> 
        >>> listener = MyListener()
        >>> loop.add(listener, "attack_roll")
        >>> loop.emit("attack_roll", args)
        Attack rolled!
    """
    
    def __init__(self) -> None:
        """Initialize empty event loop."""
        self.listeners: Dict[str, List[Listener]] = {}

    def add(
        self,
        listener: Listener,
        events: Union[List[str], str]
    ) -> None:
        """
        Register a listener for one or more events.
        
        Args:
            listener: Object that will handle events
            events: Event name(s) to listen for (string or list of strings)
            
        Example:
            >>> loop.add(my_feat, ["attack_roll", "damage_roll"])
            >>> loop.add(other_feat, "begin_turn")
        """
        # Normalize to list
        if isinstance(events, str):
            events = [events]
        
        # Register for each event
        for event in events:
            if event not in self.listeners:
                self.listeners[event] = []
            
            # Avoid duplicate registrations
            if listener not in self.listeners[event]:
                self.listeners[event].append(listener)

    def remove(self, listener: Listener) -> None:
        """
        Unregister a listener from all events.
        
        Args:
            listener: Listener to remove
        """
        for event_name in self.listeners:
            if listener in self.listeners[event_name]:
                self.listeners[event_name].remove(listener)

    def remove_from_event(self, listener: Listener, event: str) -> None:
        """
        Unregister a listener from a specific event.
        
        Args:
            listener: Listener to remove
            event: Event name to unregister from
        """
        if event in self.listeners and listener in self.listeners[event]:
            self.listeners[event].remove(listener)

    def emit(self, event: str, *args, **kwargs) -> None:
        """
        Dispatch an event to all registered listeners.
        
        Calls the method named `event` on each listener that has such
        a method, passing along any arguments.
        
        Args:
            event: Name of the event to emit
            *args: Positional arguments to pass to handlers
            **kwargs: Keyword arguments to pass to handlers
            
        Example:
            >>> loop.emit("attack_roll", attack_args)
            >>> loop.emit("damage_roll", damage_args, multiplier=2.0)
        """
        listeners = self.listeners.get(event, [])
        
        for listener in listeners:
            # Check if listener has a handler for this event
            if hasattr(listener, event):
                handler = getattr(listener, event)
                
                # Call the handler
                if callable(handler):
                    handler(*args, **kwargs)

    def has_listeners(self, event: str) -> bool:
        """
        Check if any listeners are registered for an event.
        
        Args:
            event: Event name to check
            
        Returns:
            True if at least one listener is registered
        """
        return event in self.listeners and len(self.listeners[event]) > 0

    def count_listeners(self, event: str) -> int:
        """
        Count number of listeners for an event.
        
        Args:
            event: Event name
            
        Returns:
            Number of registered listeners
        """
        return len(self.listeners.get(event, []))

    def get_events(self) -> List[str]:
        """
        Get list of all events that have listeners.
        
        Returns:
            List of event names
        """
        return list(self.listeners.keys())

    def clear(self) -> None:
        """
        Remove all listeners from all events.
        
        Useful for cleanup or reset scenarios.
        """
        self.listeners.clear()

    def clear_event(self, event: str) -> None:
        """
        Remove all listeners from a specific event.
        
        Args:
            event: Event name to clear
        """
        if event in self.listeners:
            self.listeners[event].clear()

    def __str__(self) -> str:
        """String representation showing event counts."""
        event_counts = {
            event: len(listeners)
            for event, listeners in self.listeners.items()
            if listeners
        }
        return f"EventLoop({event_counts})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        total_listeners = sum(len(l) for l in self.listeners.values())
        return (
            f"EventLoop(events={len(self.listeners)}, "
            f"total_listeners={total_listeners})"
        )


class EventContext:
    """
    Context manager for temporarily adding event listeners.
    
    Useful for effects that should only last for a specific scope.
    
    Example:
        >>> with EventContext(character.events, temp_listener, "attack_roll"):
        ...     character.attack(target, weapon)
        ... # temp_listener is automatically removed after the attack
    """
    
    def __init__(
        self,
        event_loop: EventLoop,
        listener: Listener,
        events: Union[List[str], str]
    ):
        """
        Initialize context manager.
        
        Args:
            event_loop: EventLoop to add listener to
            listener: Listener to temporarily register
            events: Event(s) to listen for
        """
        self.event_loop = event_loop
        self.listener = listener
        self.events = [events] if isinstance(events, str) else events

    def __enter__(self) -> Listener:
        """Add listener to event loop."""
        self.event_loop.add(self.listener, self.events)
        return self.listener

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Remove listener from event loop."""
        self.event_loop.remove(self.listener)
