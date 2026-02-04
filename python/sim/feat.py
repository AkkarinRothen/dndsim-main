"""
Feat system for character customization.

This module provides the base Feat class and event system for implementing
character abilities, feats, and features.
"""
from typing import TYPE_CHECKING

from sim.event_loop import Listener

if TYPE_CHECKING:
    import sim.character
    import sim.target
    import sim.events


# All possible event names that feats can respond to
EVENT_NAMES: set[str] = {
    "begin_turn",
    "before_action",
    "action",
    "after_action",
    "before_attack",
    "attack",
    "attack_roll",
    "attack_result",
    "end_turn",
    "enemy_turn",
    "short_rest",
    "long_rest",
    "weapon_roll",
    "cast_spell",
    "damage_roll",
}


class Feat(Listener):
    """
    Base class for character feats and features.
    
    Feats can react to game events by implementing methods matching
    event names (e.g., attack_roll, damage_roll). The events() method
    automatically detects which events a feat responds to.
    
    To create a custom feat:
    1. Subclass Feat
    2. Implement desired event handler methods
    3. Optionally override apply() for feat initialization
    
    Example:
        >>> class PowerAttack(Feat):
        ...     def attack_roll(self, args):
        ...         # Take -5 to hit for +10 damage
        ...         args.situational_bonus -= 5
        ...     
        ...     def damage_roll(self, args):
        ...         if args.is_weapon_damage():
        ...             args.damage.flat_dmg += 10
    
    Attributes:
        character: Character this feat is attached to
    """
    
    def name(self) -> str:
        """
        Get the feat's display name.
        
        By default uses the class name. Override for custom names.
        
        Returns:
            Feat name
        """
        return type(self).__name__

    def apply(self, character: "sim.character.Character") -> None:
        """
        Apply feat to character.
        
        Called when feat is added to character. Use this to modify
        character stats, add resources, register for events, etc.
        
        Args:
            character: Character receiving the feat
        """
        self.character = character

    def events(self) -> list[str]:
        """
        Automatically detect which events this feat responds to.
        
        Checks for methods matching event names that have been
        overridden from the base Feat class.
        
        Returns:
            List of event names this feat handles
        """
        events: list[str] = []
        
        for method_name in dir(self):
            # Check if it's a valid event name
            if method_name not in EVENT_NAMES:
                continue
            
            # Check if method was overridden from base Feat
            feat_method = getattr(Feat, method_name)
            subclass_method = getattr(type(self), method_name)
            
            if feat_method != subclass_method:
                events.append(method_name)
        
        return events

    # =============================
    #       TURN EVENTS
    # =============================

    def begin_turn(self, target: "sim.target.Target") -> None:
        """
        Called at the start of character's turn.
        
        Args:
            target: Current combat target
        """
        pass

    def end_turn(self, target: "sim.target.Target") -> None:
        """
        Called at the end of character's turn.
        
        Args:
            target: Current combat target
        """
        pass

    def before_action(self, target: "sim.target.Target") -> None:
        """
        Called before action phase.
        
        Args:
            target: Current combat target
        """
        pass

    def action(self, target: "sim.target.Target") -> None:
        """
        Called during action phase.
        
        Used to implement character's main action.
        
        Args:
            target: Current combat target
        """
        pass

    def after_action(self, target: "sim.target.Target") -> None:
        """
        Called after action phase.
        
        Args:
            target: Current combat target
        """
        pass

    def enemy_turn(self, target: "sim.target.Target") -> None:
        """
        Called during enemy's turn.
        
        Used for reactions and other out-of-turn abilities.
        
        Args:
            target: Enemy taking their turn
        """
        pass

    # =============================
    #       ATTACK EVENTS
    # =============================

    def before_attack(self) -> None:
        """
        Called before making an attack.
        
        Used for setup or conditions that apply to all attacks.
        """
        pass

    def attack(self, args: "sim.events.AttackArgs") -> None:
        """
        Called when making an attack.
        
        Args:
            args: Attack arguments
        """
        pass

    def attack_roll(self, args: "sim.events.AttackRollArgs") -> None:
        """
        Called when rolling to hit.
        
        Modify args to add advantage/disadvantage or bonuses.
        
        Args:
            args: Attack roll arguments
        """
        pass

    def attack_result(self, args: "sim.events.AttackResultArgs") -> None:
        """
        Called after attack roll is resolved.
        
        Add damage, apply effects based on hit/miss/crit.
        
        Args:
            args: Attack result with hit/miss/crit info
        """
        pass

    # =============================
    #       DAMAGE EVENTS
    # =============================

    def damage_roll(self, args: "sim.events.DamageRollArgs") -> None:
        """
        Called when rolling damage.
        
        Modify damage dice or add flat damage.
        
        Args:
            args: Damage roll arguments
        """
        pass

    # =============================
    #       SPELL EVENTS
    # =============================

    def cast_spell(self, args: "sim.events.CastSpellArgs") -> None:
        """
        Called when casting a spell.
        
        Args:
            args: Spell casting arguments
        """
        pass

    # =============================
    #       REST EVENTS
    # =============================

    def short_rest(self) -> None:
        """
        Called during short rest.
        
        Reset short rest resources, clear temporary effects.
        """
        pass

    def long_rest(self) -> None:
        """
        Called during long rest.
        
        Reset all resources, remove conditions.
        """
        pass

    # =============================
    #       WEAPON EVENTS
    # =============================

    def weapon_roll(self, args: "sim.events.AttackRollArgs") -> None:
        """
        Called when rolling with a weapon.
        
        Deprecated: Use attack_roll instead.
        
        Args:
            args: Attack roll arguments
        """
        pass

    def __str__(self) -> str:
        """String representation."""
        return self.name()

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}()"


class ConditionalFeat(Feat):
    """
    Base class for feats that only apply under certain conditions.
    
    Subclasses should implement is_active() to determine when the
    feat's effects apply.
    
    Example:
        >>> class RecklessAttack(ConditionalFeat):
        ...     def __init__(self):
        ...         self.active = False
        ...     
        ...     def is_active(self):
        ...         return self.active
        ...     
        ...     def attack_roll(self, args):
        ...         if self.is_active():
        ...             args.adv = True
    """
    
    def is_active(self) -> bool:
        """
        Check if feat is currently active.
        
        Returns:
            True if feat should apply its effects
        """
        return True


class PassiveFeat(Feat):
    """
    Base class for passive feats with no active effects.
    
    Used for feats that only modify character during apply(),
    such as stat increases or proficiency grants.
    
    Example:
        >>> class ToughFeat(PassiveFeat):
        ...     def apply(self, character):
        ...         super().apply(character)
        ...         # Add 2 HP per level
        ...         character.max_hp += 2 * character.level
        ...         character.hp += 2 * character.level
    """
    pass
