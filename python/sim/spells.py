"""
Spellcasting system for D&D 5e.

This module implements spell slots, concentration, spellcaster progression,
and base spell classes.
"""
from typing import List, Tuple, Optional, TYPE_CHECKING
import math
from enum import Enum

from util.log import log
from util.util import spell_slots, highest_spell_slot, lowest_spell_slot
import util.taggable
import sim.event_loop
from sim.resource import WarlockPactSlots

if TYPE_CHECKING:
    import sim.target
    import sim.character
    import sim.attack



class Spellcaster(Enum):
    """
    Spellcaster progression type.
    
    Determines how spell slots scale with class level.
    """
    FULL = 0    # Wizard, Cleric, Druid, etc.
    HALF = 1    # Paladin, Ranger
    THIRD = 2   # Eldritch Knight, Arcane Trickster
    NONE = 3    # Non-spellcasters


def spellcaster_level(levels: List[Tuple[Spellcaster, int]]) -> int:
    """
    Calculate effective spellcaster level for multiclassing.
    
    Full casters contribute their full level, half casters contribute
    half (rounded up), and third casters contribute one-third (rounded up).
    
    Args:
        levels: List of (spellcaster_type, class_level) tuples
        
    Returns:
        Total effective spellcaster level
        
    Examples:
        >>> # Wizard 5 / Fighter 3
        >>> spellcaster_level([(Spellcaster.FULL, 5), (Spellcaster.NONE, 3)])
        5
        >>> 
        >>> # Wizard 3 / Paladin 4
        >>> spellcaster_level([(Spellcaster.FULL, 3), (Spellcaster.HALF, 4)])
        5
    """
    total = 0
    
    for caster_type, level in levels:
        if caster_type is Spellcaster.FULL:
            total += level
        elif caster_type is Spellcaster.HALF:
            total += math.ceil(float(level) / 2)
        elif caster_type is Spellcaster.THIRD:
            total += math.ceil(float(level) / 3)
        # NONE adds nothing
    
    return total


class Spellcasting(sim.event_loop.Listener):
    """
    Manages character's spellcasting and spell slots.
    
    Tracks spell slots (both regular and Pact Magic), concentration,
    active spells, and provides methods for casting.
    
    Attributes:
        character: Character that owns this spellcasting
        mod: Spellcasting ability ('int', 'wis', 'cha', etc.)
        spellcaster_levels: List of (type, level) for multiclassing
        concentration: Spell currently being concentrated on
        spells: List of active spells
        pact_slots_resource: WarlockPactSlots resource for Pact Magic
        to_hit_bonus: Additional bonus to spell attack rolls
    """
    
    def __init__(
        self,
        character: "sim.character.Character",
        mod: str,
        spellcaster_levels: List[Tuple[Spellcaster, int]],
    ) -> None:
        """
        Initialize spellcasting system.
        
        Args:
            character: Character that casts spells
            mod: Spellcasting ability modifier
            spellcaster_levels: Spellcaster type and level
        """
        self.character = character
        self.mod = mod
        self.spellcaster_levels = spellcaster_levels
        
        self.concentration: Optional["Spell"] = None
        self.spells: List["Spell"] = [] # Active spells
        self.known_spells: List["Spell"] = []
        self.slots: List[int] = []
        self.pact_slots_resource: Optional[WarlockPactSlots] = None
        self.to_hit_bonus = 0
        
        # Register for rest events
        character.events.add(self, ["short_rest", "long_rest"])

    def add_spell(self, spell: "Spell") -> None:
        """Adds a spell to the list of known spells."""
        self.known_spells.append(spell)

    def add_spellcaster_level(self, spellcaster: Spellcaster, level: int) -> None:
        """
        Add spellcaster levels (for multiclassing).
        
        Args:
            spellcaster: Type of spellcaster
            level: Number of levels
        """
        self.spellcaster_levels.append((spellcaster, level))

    def add_pact_spellcaster_level(self, level: int) -> None:
        """
        Add Warlock levels for Pact Magic or update existing Pact Slots resource.
        
        Args:
            level: Number of Warlock levels
        """
        if not self.pact_slots_resource:
            # max_uses is a dummy value, WarlockPactSlots calculates its own max
            self.character.add_resource("Pact Slots", max_uses=0, warlock_level=level)
            self.pact_slots_resource = self.character.resources.get("Pact Slots")
        else:
            self.pact_slots_resource.increase_max(level) # increase_max in WarlockPactSlots takes level directly

    def long_rest(self) -> None:
        """
        Recover all spell slots and end concentration on long rest.
        """
        # Recover regular spell slots
        self.slots = spell_slots(spellcaster_level(self.spellcaster_levels))
        
        self.short_rest()

    def short_rest(self) -> None:
        """
        Recover pact slots and end concentration on short rest.
        """
        # Warlock slots recover on short rest
        if self.pact_slots_resource:
            self.pact_slots_resource.reset()
        
        # End concentration
        self.set_concentration(None)
        
        # End all active spells
        for spell in self.spells[:]:  # Copy list to avoid modification during iteration
            spell.end(self.character)
        self.spells.clear()

    def dc(self) -> int:
        """
        Calculate spell save DC.
        
        Formula: 8 + proficiency + spellcasting modifier
        
        Returns:
            Spell save DC
        """
        return 8 + self.character.mod(self.mod) + self.character.prof

    def to_hit(self) -> int:
        """
        Calculate spell attack bonus.
        
        Formula: proficiency + spellcasting modifier + bonuses
        
        Returns:
            Spell attack bonus
        """
        return (
            self.character.mod(self.mod) +
            self.character.prof +
            self.to_hit_bonus
        )

    def has_slot(self, level: int) -> bool:
        """
        Check if a spell slot is available.
        
        Checks both regular and pact slots.
        
        Args:
            level: Spell level (1-9)
            
        Returns:
            True if slot is available
        """
        # Check regular slots
        if level < len(self.slots) and self.slots[level] > 0:
            return True
        
        # Check pact slots
        if self.pact_slots_resource and self.pact_slots_resource.has(1):
            return self.pact_slots_resource.get_slot_level() >= level
        
        return False

    def pact_slot(self, max_slot: int = 9, min_slot: int = 1) -> int:
        """
        Get available Pact Magic slot level.
        
        Args:
            max_slot: Maximum slot level to consider
            min_slot: Minimum slot level to consider
            
        Returns:
            Pact slot level (0 if none available)
        """
        if self.pact_slots_resource and self.pact_slots_resource.has(1):
            slot = self.pact_slots_resource.get_slot_level()
            if min_slot <= slot <= max_slot:
                return slot
        return 0

    def highest_slot(self, max_slot: int = 9) -> int:
        """
        Get highest available spell slot level.
        
        Args:
            max_slot: Maximum slot level to consider
            
        Returns:
            Highest slot level available
        """
        regular_slot = highest_spell_slot(self.slots, max=max_slot)
        pact_slot = self.pact_slot(max_slot=max_slot)
        return max(regular_slot, pact_slot)

    def lowest_slot(self, min_slot: int = 1) -> int:
        """
        Get lowest available spell slot level.
        
        Args:
            min_slot: Minimum slot level to consider
            
        Returns:
            Lowest slot level available
        """
        regular_slot = lowest_spell_slot(self.slots, min=min_slot)
        pact_slot = self.pact_slot(min_slot=min_slot)
        
        if regular_slot == 0:
            return pact_slot
        if pact_slot == 0:
            return regular_slot
        
        return min(regular_slot, pact_slot)

    def cast(
        self,
        spell: "Spell",
        target: Optional["sim.target.Target"] = None,
        ignore_slot: bool = False,
    ) -> None:
        """
        Cast a spell, consuming a spell slot.
        
        Args:
            spell: Spell to cast
            target: Target of the spell
            ignore_slot: If True, don't consume a slot (e.g., for cantrips)
        """
        log.record(f"Cast ({spell.name})", 1)
        
        # Consume spell slot
        if spell.slot > 0 and not ignore_slot:
            # Try pact slot first
            if self.pact_slots_resource and self.pact_slot() == spell.slot:
                if not self.pact_slots_resource.use(1, detail=spell.name):
                    raise ValueError(
                        f"Not enough Pact Slots available for {spell.name} (level {spell.slot})"
                    )
            # Try regular slot
            elif spell.slot < len(self.slots) and self.slots[spell.slot] > 0:
                self.slots[spell.slot] -= 1
            else:
                raise ValueError(
                    f"No spell slot available for {spell.name} (level {spell.slot})"
                )
        
        # Handle concentration
        if spell.concentration:
            self.set_concentration(spell)
        
        # Cast the spell
        spell.cast(self.character, target)
        
        # Track active spells
        if spell.duration > 0 or spell.concentration:
            self.spells.append(spell)

    def end_spell(self, spell: "Spell") -> None:
        """
        End an active spell.
        
        Args:
            spell: Spell to end
        """
        if spell in self.spells:
            self.spells.remove(spell)
        spell.end(self.character)

    def set_concentration(self, spell: Optional["Spell"]) -> None:
        """
        Set concentration to a new spell.
        
        Automatically ends previous concentration if any.
        
        Args:
            spell: Spell to concentrate on (None to end concentration)
        """
        # End previous concentration
        if self.concentration:
            if self.concentration in self.spells:
                self.spells.remove(self.concentration)
            self.concentration.end(self.character)
        
        self.concentration = spell

    def concentrating_on(self, name: str) -> bool:
        """
        Check if concentrating on a specific spell.
        
        Args:
            name: Spell name
            
        Returns:
            True if currently concentrating on that spell
        """
        return self.concentration is not None and self.concentration.name == name

    def is_concentrating(self) -> bool:
        """
        Check if concentrating on any spell.
        
        Returns:
            True if concentration is active
        """
        return self.concentration is not None

    def cantrip_dice(self) -> int:
        """
        Get number of damage dice for cantrips.
        
        Cantrip damage scales at levels 5, 11, and 17.
        
        Returns:
            Number of dice (1-4)
        """
        if self.character.level >= 17:
            return 4
        elif self.character.level >= 11:
            return 3
        elif self.character.level >= 5:
            return 2
        return 1

    def __str__(self) -> str:
        """String representation showing slots."""
        slot_str = "/".join(str(s) for s in self.slots[1:] if s > 0)
        if self.pact_slots_resource and self.pact_slots_resource.num_slots > 0:
            pact_str = f" + {self.pact_slots_resource.num}/{self.pact_slots_resource.num_slots}x{self.pact_slots_resource.slot_level}th (pact)"
        else:
            pact_str = ""
        return f"Spell Slots: {slot_str}{pact_str}"

"""
Spell classes for D&D 5e - Part 2.

This file contains the Spell base class and common spell types.
Combine with spells_part1.py for the complete module.
"""
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

import util.taggable

if TYPE_CHECKING:
    import sim.character
    import sim.target
    import sim.attack


class School(Enum):
    """
    Schools of magic in D&D 5e.
    """
    ABJURATION = 1
    CONJURATION = 2
    DIVINATION = 3
    ENCHANTMENT = 4
    EVOCATION = 5
    ILLUSION = 6
    NECROMANCY = 7
    TRANSMUTATION = 8


class Spell(util.taggable.Taggable):
    """
    Base class for all spells.
    
    Provides common spell attributes and methods. Subclass this to
    create specific spell implementations.
    
    Attributes:
        name: Spell name
        slot: Spell level (0 for cantrips, 1-9 for leveled spells)
        concentration: Whether spell requires concentration
        duration: Duration in rounds (0 for instantaneous)
        school: School of magic
        damage_type: Type of damage dealt (if applicable)
        character: Character who cast the spell (set during casting)
    """
    
    def __init__(
        self,
        name: str,
        slot: int,
        concentration: bool = False,
        duration: int = 0,
        school: Optional[School] = None,
        damage_type: str = "physical",
    ):
        """
        Initialize spell.
        
        Args:
            name: Spell name
            slot: Spell level (0-9)
            concentration: Whether spell requires concentration
            duration: Duration in rounds
            school: School of magic
            damage_type: Damage type if spell deals damage
            
        Raises:
            ValueError: If slot is not 0-9
        """
        if not 0 <= slot <= 9:
            raise ValueError(f"Spell slot must be 0-9, got {slot}")
        
        super().__init__()
        
        self.name = name
        self.slot = slot
        self.concentration = concentration
        self.duration = duration
        self.school = school
        self.damage_type = damage_type
        self.character: Optional["sim.character.Character"] = None

    def cast(
        self,
        character: "sim.character.Character",
        target: Optional["sim.target.Target"] = None,
    ) -> None:
        """
        Cast the spell.
        
        Override this in subclasses to implement spell effects.
        
        Args:
            character: Character casting the spell
            target: Target of the spell (if applicable)
        """
        self.character = character

    def end(self, character: "sim.character.Character") -> None:
        """
        End the spell's effects.
        
        Called when duration expires or concentration breaks.
        Override to implement cleanup.
        
        Args:
            character: Character who cast the spell
        """
        pass

    def is_cantrip(self) -> bool:
        """Check if spell is a cantrip."""
        return self.slot == 0

    def __str__(self) -> str:
        """String representation."""
        level_str = "Cantrip" if self.slot == 0 else f"Level {self.slot}"
        return f"{self.name} ({level_str})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Spell(name='{self.name}', slot={self.slot}, "
            f"concentration={self.concentration})"
        )


class TargetedSpell(Spell):
    """
    Base class for spells that target a specific creature.
    
    Automatically calls cast_target() when cast with a target.
    """
    
    def cast(
        self,
        character: "sim.character.Character",
        target: Optional["sim.target.Target"] = None,
    ) -> None:
        """
        Cast spell and call cast_target if target exists.
        
        Args:
            character: Caster
            target: Target creature
        """
        super().cast(character, target)
        
        if target:
            self.cast_target(character, target)

    def cast_target(
        self,
        character: "sim.character.Character",
        target: "sim.target.Target"
    ) -> None:
        """
        Apply spell effects to target.
        
        Override this to implement targeted spell effects.
        
        Args:
            character: Caster
            target: Target creature
        """
        pass


class ConcentrationSpell(Spell):
    """
    Base class for spells requiring concentration.
    
    Automatically adds/removes an effect with the spell's name
    to/from the character.
    """
    
    def __init__(self, name: str, slot: int, **kwargs):
        """
        Initialize concentration spell.
        
        Args:
            name: Spell name
            slot: Spell level
            **kwargs: Additional Spell arguments
        """
        super().__init__(name, slot, concentration=True, **kwargs)

    def cast(
        self,
        character: "sim.character.Character",
        target: Optional["sim.target.Target"] = None,
    ) -> None:
        """
        Cast spell and add effect to character.
        
        Args:
            character: Caster
            target: Target (if applicable)
        """
        super().cast(character, target)
        character.add_effect(self.name)

    def end(self, character: "sim.character.Character") -> None:
        """
        End concentration and remove effect.
        
        Args:
            character: Caster
        """
        super().end(character)
        character.remove_effect(self.name)


class BasicSaveSpell(Spell):
    """
    Spell that requires a saving throw and deals damage.
    
    Target makes a save; on success takes half damage,
    on failure takes full damage.
    """
    
    def __init__(
        self,
        name: str,
        slot: int,
        dice: List[int],
        save_ability: str,
        flat_dmg: int = 0,
        damage_type: str = "physical",
        **kwargs
    ):
        """
        Initialize save spell.
        
        Args:
            name: Spell name
            slot: Spell level
            dice: Damage dice (e.g., [8, 8] for 2d8)
            save_ability: Ability for save ('dex', 'con', etc.)
            flat_dmg: Flat damage to add
            damage_type: Type of damage
            **kwargs: Additional Spell arguments
        """
        super().__init__(name, slot, damage_type=damage_type, **kwargs)
        self.dice = dice
        self.save_ability = save_ability
        self.flat_dmg = flat_dmg

    def cast(
        self,
        character: "sim.character.Character",
        target: Optional["sim.target.Target"] = None,
    ) -> None:
        """
        Cast spell and have target make save.
        
        Args:
            character: Caster
            target: Target making the save
        """
        if not target:
            return
        
        super().cast(character, target)
        
        # Target makes save
        dc = character.spells.dc()
        saved = target.save(self.save_ability, dc)
        
        # Deal damage (half if saved)
        import sim.attack
        character.do_damage(
            target,
            damage=sim.attack.DamageRoll(
                source=self.name,
                dice=self.dice,
                flat_dmg=self.flat_dmg,
                damage_type=self.damage_type,
            ),
            spell=self,
            multiplier=0.5 if saved else 1.0,
        )


class AttackSpell(Spell):
    """
    Spell that makes a spell attack roll.
    
    Uses character.spell_attack() to make the attack.
    """
    
    def __init__(
        self,
        name: str,
        slot: int,
        dice: List[int],
        flat_dmg: int = 0,
        damage_type: str = "physical",
        is_ranged: bool = True,
        **kwargs
    ):
        """
        Initialize attack spell.
        
        Args:
            name: Spell name
            slot: Spell level
            dice: Damage dice
            flat_dmg: Flat damage
            damage_type: Type of damage
            is_ranged: Whether spell attack is ranged
            **kwargs: Additional Spell arguments
        """
        super().__init__(name, slot, damage_type=damage_type, **kwargs)
        self.dice = dice
        self.flat_dmg = flat_dmg
        self.ranged = is_ranged

    def cast(
        self,
        character: "sim.character.Character",
        target: Optional["sim.target.Target"] = None,
    ) -> None:
        """
        Cast spell and make attack roll.
        
        Args:
            character: Caster
            target: Target to attack
        """
        if not target:
            return
        
        super().cast(character, target)
        
        # Make spell attack
        import sim.attack
        damage = sim.attack.DamageRoll.from_dice_notation(
            source=self.name,
            num_dice=len(self.dice),
            die=self.dice[0] if self.dice else 0,
            flat_dmg=self.flat_dmg,
            damage_type=self.damage_type,
        )
        
        character.spell_attack(
            target=target,
            spell=self,
            damage=damage,
            is_ranged=self.ranged,
        )


class BuffSpell(ConcentrationSpell):
    """
    Spell that provides a buff to the caster or ally.
    
    Extend this class and override apply_buff() and remove_buff()
    to implement specific buff effects.
    """
    
    def cast(
        self,
        character: "sim.character.Character",
        target: Optional["sim.target.Target"] = None,
    ) -> None:
        """
        Cast spell and apply buff.
        
        Args:
            character: Caster (usually also the target)
            target: Optional target
        """
        super().cast(character, target)
        self.apply_buff(character)

    def end(self, character: "sim.character.Character") -> None:
        """
        End spell and remove buff.
        
        Args:
            character: Character with buff
        """
        self.remove_buff(character)
        super().end(character)

    def apply_buff(self, character: "sim.character.Character") -> None:
        """
        Apply buff effects.
        
        Override this to implement buff.
        
        Args:
            character: Character receiving buff
        """
        pass

    def remove_buff(self, character: "sim.character.Character") -> None:
        """
        Remove buff effects.
        
        Override this to implement buff removal.
        
        Args:
            character: Character losing buff
        """
        pass


class AreaSpell(Spell):
    """
    Spell that affects an area with multiple targets.
    
    Currently simplified to affect a single target, but can be
    extended for true multi-target support.
    """
    
    def __init__(
        self,
        name: str,
        slot: int,
        save_ability: str,
        dice: List[int],
        flat_dmg: int = 0,
        damage_type: str = "physical",
        **kwargs
    ):
        """
        Initialize area spell.
        
        Args:
            name: Spell name
            slot: Spell level
            save_ability: Save ability
            dice: Damage dice
            flat_dmg: Flat damage
            damage_type: Damage type
            **kwargs: Additional arguments
        """
        super().__init__(name, slot, damage_type=damage_type, **kwargs)
        self.save_ability = save_ability
        self.dice = dice
        self.flat_dmg = flat_dmg

    def cast(
        self,
        character: "sim.character.Character",
        target: Optional["sim.target.Target"] = None,
    ) -> None:
        """
        Cast area spell.
        
        Args:
            character: Caster
            target: Primary target
        """
        if not target:
            return
        
        super().cast(character, target)
        
        # Have target make save
        dc = character.spells.dc()
        saved = target.save(self.save_ability, dc)
        
        # Deal damage
        import sim.attack
        character.do_damage(
            target,
            damage=sim.attack.DamageRoll(
                source=self.name,
                dice=self.dice,
                flat_dmg=self.flat_dmg,
                damage_type=self.damage_type,
            ),
            spell=self,
            multiplier=0.5 if saved else 1.0,
        )
