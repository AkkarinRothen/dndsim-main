"""
Character class for D&D 5e combat simulation.

This module implements the core Character class with stats, abilities,
spellcasting, feats, resources, and combat mechanics.
"""
from typing import Dict, List, Optional, Set, TYPE_CHECKING
from collections import defaultdict # Added for resource tracking
from dataclasses import dataclass
import math

import sim.bardic_inspiration
import sim.maneuvers
from util.util import prof_bonus
from sim.core_feats import Vex, Topple, Graze
from sim.events import AttackRollArgs, AttackArgs, AttackResultArgs
from sim.event_loop import EventLoop
from util.log import log
from sim.spells import Spellcasting, Spellcaster
from sim.attack import WeaponAttack, SpellAttack
import sim.resource
from sim.resource import WarlockPactSlots # Import WarlockPactSlots


if TYPE_CHECKING:
    import sim.events
    import sim.attack
    import sim.spells
    import sim.weapons
    import sim.feat
    import sim.target


# Constants
STATS = ["str", "dex", "con", "int", "wis", "cha"]
DEFAULT_STAT_MAX = 20
DEFAULT_AC = 15
BASE_HP = 10
HP_PER_LEVEL = 6


@dataclass
class CharacterStats:
    """Container for character ability scores."""
    str: int = 10
    dex: int = 10
    con: int = 10
    int: int = 10
    wis: int = 10
    cha: int = 10
    
    def to_dict(self) -> Dict[str, int]:
        """Convert stats to dictionary format."""
        return {
            "str": self.str,
            "dex": self.dex,
            "con": self.con,
            "int": self.int,
            "wis": self.wis,
            "cha": self.cha,
        }


class Character:
    """
    Represents a D&D 5e character with combat capabilities.
    
    Tracks stats, HP, AC, spells, feats, resources, and handles combat actions
    including attacks, damage, and turn-based gameplay.
    
    Attributes:
        name: Character display name
        level: Character level (1-20)
        prof: Proficiency bonus
        stats: Ability scores dictionary
        stat_max: Maximum values for each ability score
        ac: Armor Class
        hp: Current hit points
        max_hp: Maximum hit points
        spells: Spellcasting system
        masteries: Known weapon masteries
        feats: List of character feats
        resources: Custom resources (Ki, Channel Divinity, etc.)
    """
    
    def __init__(
        self,
        level: int,
        stats: List[int],
        base_feats: Optional[List["sim.feat.Feat"]] = None,
        spellcaster: Spellcaster = Spellcaster.NONE,
        spell_mod: str = "none",
        name: str = "Unnamed Character",
        ac: Optional[int] = None,
    ) -> None:
        """
        Initialize a new character.
        
        Args:
            level: Character level (1-20)
            stats: List of 6 ability scores [STR, DEX, CON, INT, WIS, CHA]
            base_feats: Initial feats to apply
            spellcaster: Spellcaster type
            spell_mod: Spellcasting ability modifier
            name: Character name
            ac: Armor Class (uses default if None)
            
        Raises:
            ValueError: If stats list is not length 6 or level is invalid
        """
        if len(stats) != 6:
            raise ValueError(f"Stats must have 6 values, got {len(stats)}")
        
        if not 1 <= level <= 20:
            raise ValueError(f"Level must be 1-20, got {level}")
        
        base_feats = base_feats or []
        
        # Basic attributes
        self.name: str = name
        self.level = level
        self.prof = prof_bonus(level)
        
        # Ability scores
        self.stats = {
            "str": stats[0],
            "dex": stats[1],
            "con": stats[2],
            "int": stats[3],
            "wis": stats[4],
            "cha": stats[5],
        }
        self.stat_max = {stat: DEFAULT_STAT_MAX for stat in STATS}
        
        # Combat stats
        self.ac = ac if ac is not None else DEFAULT_AC
        self.max_hp = self._calculate_max_hp()
        self.hp = self.max_hp
        
        # Combat state
        self.actions = 1
        self.used_bonus = False
        self.current_round = 0
        self.poisoned = False
        
        # Effects and minions
        self.minions: List[Character] = []
        self.effects: Set[str] = set()
        
        # Systems
        self.events = EventLoop()
        self.spells = Spellcasting(self, spell_mod, [(spellcaster, level)])
        self.masteries: Set[str] = set()
        self.class_levels: Dict[str, int] = dict()
        self.resources: Dict[str, "sim.resource.Resource"] = dict()
        self.metamagics: Set[str] = set()
        self.maneuvers = sim.maneuvers.Maneuvers(self)
        
        # Feats
        self.feats: List["sim.feat.Feat"] = []
        
        # Add core weapon mastery feats
        for feat in [Vex(), Topple(), Graze()]:
            self.add_feat(feat)
        
        # Add custom feats
        for feat in base_feats:
            self.add_feat(feat)

    @property
    def threat_rating(self) -> int:
        """
        Calculates a numerical threat rating for AI targeting.
        
        Heuristic based on class:
        - High Threat (3): Martial high-damage dealers
        - Medium Threat (2): Glass cannons and versatile damage dealers
        - Low Threat (1): Support, healers, and controllers
        
        Returns:
            An integer representing the character's threat level.
        """
        class_name = self.__class__.__name__.lower()
        
        # High threat classes
        if any(c in class_name for c in ['barbarian', 'fighter', 'paladin', 'ranger']):
            return 3
        
        # Medium threat classes
        if any(c in class_name for c in ['rogue', 'warlock', 'wizard', 'sorcerer']):
            return 2
            
        # Low threat classes (default)
        return 1

    def _calculate_max_hp(self) -> int:
        """
        Calculate maximum HP based on level and CON modifier.
        
        Formula: BASE_HP + (level - 1) * HP_PER_LEVEL + CON_mod * level
        
        Returns:
            Maximum hit points
        """
        con_mod = self.mod('con')
        return BASE_HP + ((self.level - 1) * HP_PER_LEVEL) + (con_mod * self.level)

    # =============================
    #       LIFECYCLE EVENTS
    # =============================
    
    def long_rest(self) -> None:
        """
        Take a long rest, resetting all resources and HP.
        """
        self.hp = self.max_hp
        self.poisoned = False
        self.events.emit("long_rest")
        self.short_rest()

    def short_rest(self) -> None:
        """
        Take a short rest, resetting short rest resources.
        """
        self.poisoned = False
        self.events.emit("short_rest")

    def copy(self):
        """Returns a copy of the character."""
        import copy
        return copy.deepcopy(self)

    # =============================
    #       ABILITY SCORES
    # =============================

    def stat(self, stat: str) -> int:
        """
        Get raw ability score.
        
        Args:
            stat: Ability name ("str", "dex", etc.) or "none"
            
        Returns:
            Ability score value (10 if "none")
        """
        if stat == "none":
            return 10
        return self.stats.get(stat, 10)

    def mod(self, stat: str) -> int:
        """
        Calculate ability modifier from stat.
        
        Args:
            stat: Ability name or "none"
            
        Returns:
            Ability modifier (0 if "none")
        """
        if stat == "none":
            return 0
        stat_value = self.stats.get(stat, 10)
        return (stat_value - 10) // 2

    def increase_stat_max(self, stat: str, amount: int) -> None:
        """
        Increase maximum value for an ability score.
        
        Args:
            stat: Ability name
            amount: Amount to increase maximum by
        """
        if stat == "none" or stat not in STATS:
            return
        self.stat_max[stat] += amount

    def increase_stat(self, stat: str, amount: int) -> None:
        """
        Increase ability score, respecting maximum.
        
        Args:
            stat: Ability name
            amount: Amount to increase by
        """
        if stat == "none" or stat not in STATS:
            return
        
        new_val = self.stats[stat] + amount
        max_val = self.stat_max[stat]
        
        self.stats[stat] = min(new_val, max_val)

    def dc(self, stat: str) -> int:
        """
        Calculate save DC for abilities using this stat.
        
        Formula: 8 + proficiency + ability modifier
        
        Args:
            stat: Ability name
            
        Returns:
            Difficulty Class
        """
        return 8 + self.prof + self.mod(stat)

    # =============================
    #       DAMAGE & HP
    # =============================

    def apply_damage(self, damage: int, damage_type: str, source: str) -> None:
        """
        Apply damage to character, reducing HP.
        
        Currently doesn't handle resistances/immunities.
        
        Args:
            damage: Amount of damage
            damage_type: Type of damage (for future resistance handling)
            source: Source of damage (for logging)
        """
        self.hp -= damage
        
        if self.hp <= 0:
            log.record(f"{self.name} Unconscious", 1)

    # =============================
    #       FEATS & ABILITIES
    # =============================

    def add_feat(self, feat: "sim.feat.Feat") -> None:
        """
        Add a feat to character and register its events.
        
        Args:
            feat: Feat to add
        """
        feat.apply(self)
        self.feats.append(feat)
        self.events.add(feat, feat.events())

    def has_feat(self, name: str) -> bool:
        """
        Check if character has a specific feat.
        
        Args:
            name: Feat name
            
        Returns:
            True if feat is present
        """
        return any(feat.__class__.__name__ == name for feat in self.feats)

    # =============================
    #       CLASS LEVELS
    # =============================

    def add_class_level(self, class_name: str, level: int) -> None:
        """
        Set character's level in a specific class.
        
        Args:
            class_name: Name of class
            level: Level in that class
        """
        self.class_levels[class_name] = level

    def has_class_level(self, class_name: str, level: int) -> bool:
        """
        Check if character has at least a certain level in a class.
        
        Args:
            class_name: Name of class
            level: Minimum level to check
            
        Returns:
            True if character has sufficient levels
        """
        return (
            class_name in self.class_levels
            and self.class_levels[class_name] >= level
        )

    # =============================
    #       RESOURCES
    # =============================

    def add_resource(self, name: str, max_uses: int, short_rest: bool = False, **kwargs) -> None:
        """
        Add a custom resource to character.
        
        Args:
            name: Resource name
            max_uses: Maximum number of uses
            short_rest: Whether resource recharges on short rest
            **kwargs: Additional arguments for specialized resource constructors
        """
        if name == "Bardic Inspiration":
            resource = sim.bardic_inspiration.BardicInspiration(self, name, short_rest, kwargs.get('die_size', 6))
        elif name == "Pact Slots":
            resource = WarlockPactSlots(self, kwargs.get('warlock_level', 0))
        else:
            resource = sim.resource.Resource(self, name, short_rest)
        
        if name != "Pact Slots": # WarlockPactSlots handles its own max and reset
            resource.increase_max(max_uses)
            resource.reset()
        self.resources[name] = resource

    def has_resource(self, name: str) -> bool:
        """
        Check if character has uses of a resource available.
        
        Args:
            name: Resource name
            
        Returns:
            True if resource exists and has uses remaining
        """
        return name in self.resources and self.resources[name].has()

    def use_bonus(self, source: str) -> bool:
        """
        Attempt to use bonus action.
        
        Args:
            source: What is using the bonus action
            
        Returns:
            True if bonus action was available and used
        """
        if not self.used_bonus:
            log.record(f"Bonus ({source})", 1)
            self.used_bonus = True
            return True
        return False

    # =============================
    #       EFFECTS & MINIONS
    # =============================

    def add_effect(self, effect: str) -> None:
        """Add a status effect to character."""
        self.effects.add(effect)

    def remove_effect(self, effect: str) -> None:
        """Remove a status effect from character."""
        self.effects.discard(effect)

    def has_effect(self, effect: str) -> bool:
        """Check if character has a status effect."""
        return effect in self.effects

    def add_minion(self, minion: "Character") -> None:
        """Add a minion that acts with this character."""
        self.minions.append(minion)

    def remove_minion(self, minion: "Character") -> None:
        """Remove a minion."""
        if minion in self.minions:
            self.minions.remove(minion)

    # =============================
    #       LIFECYCLE EVENTS
    # =============================

    def begin_turn(self, target: "sim.target.Target", round_number: int = 0, combat=None) -> None:
        """
        Start character's turn.
        
        Args:
            target: Current combat target
            round_number: The current round number
            combat: The combat instance for logging
        """
        self.current_round = round_number
        log.record("Turn", 1)
        self.actions = 1
        self.used_bonus = False
        self.events.emit("begin_turn", target)

    def end_turn(self, target: "sim.target.Target") -> None:
        """
        End character's turn.
        
        Args:
            target: Current combat target
        """
        self.events.emit("end_turn", target)
        
        if not self.used_bonus:
            log.record("Bonus (None)", 1)

    def turn(self, target: "sim.target.Target", round_number: int = 0, combat=None) -> None:
        """
        Execute full character turn including minions.
        
        Args:
            target: Combat target
            round_number: The current round number
            combat: The combat instance for logging
        """
        self.begin_turn(target, round_number=round_number, combat=combat)
        self.events.emit("before_action", target)
        
        while self.actions > 0:
            self.events.emit("action", target)
            self.actions -= 1
        
        self.events.emit("after_action", target)
        self.end_turn(target)
        
        # Minions take their turns
        for minion in self.minions:
            minion.turn(target, round_number=round_number, combat=combat)

    def short_rest(self) -> None:
        """Take a short rest, recovering some resources."""
        self.effects.clear()
        self.events.emit("short_rest")

    def long_rest(self) -> None:
        """Take a long rest, fully recovering HP and all resources."""
        self.hp = self.max_hp
        self.short_rest()
        self.events.emit("long_rest")

    def enemy_turn(self, target: "sim.target.Target") -> None:
        """
        React to enemy's turn.
        
        Args:
            target: The enemy taking their turn
        """
        self.events.emit("enemy_turn", target)

    # ============================
    #      ATTACKS
    # ============================

    def weapon_attack(
        self,
        target: "sim.target.Target",
        weapon: "sim.weapons.Weapon",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Make a weapon attack.
        
        Args:
            target: Target to attack
            weapon: Weapon being used
            tags: Optional attack tags
        """
        attack = WeaponAttack(weapon)
        self.attack(target=target, attack=attack, weapon=weapon, tags=tags)

    def spell_attack(
        self,
        target: "sim.target.Target",
        spell: "sim.spells.Spell",
        damage: Optional["sim.attack.DamageRoll"] = None,
        callback: Optional[callable] = None,
        is_ranged: bool = False,
    ) -> None:
        """
        Make a spell attack roll.
        
        Args:
            target: Target to attack
            spell: Spell being cast
            damage: Damage roll for spell
            callback: Optional callback for effects
            is_ranged: Whether spell attack is ranged
        """
        attack = SpellAttack(
            spell,
            callback=callback,
            is_ranged=is_ranged,
            damage=damage,
        )
        self.attack(target=target, attack=attack, spell=spell)

    def attack(
        self,
        target: "sim.target.Target",
        attack: "sim.attack.Attack",
        weapon: Optional["sim.weapons.Weapon"] = None,
        spell: Optional["sim.spells.Spell"] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Execute a complete attack sequence.
        
        Handles attack roll, hit/miss, critical hits, and damage application.
        
        Args:
            target: Target being attacked
            attack: Attack object (weapon or spell)
            weapon: Weapon if weapon attack
            spell: Spell if spell attack
            tags: Optional attack tags
        """
        args = AttackArgs(
            target=target,
            attack=attack,
            weapon=weapon,
            spell=spell,
            tags=tags
        )
        
        log.record(f"Attack ({args.attack.name})", 1)
        self.events.emit("before_attack")
        
        # Roll to hit
        to_hit = args.attack.to_hit(self)
        roll_result = self.attack_roll(attack=args, to_hit=to_hit)
        roll = roll_result.roll()
        
        # Determine crit threshold
        min_crit = (
            args.attack.min_crit()
            if roll_result.min_crit is None
            else roll_result.min_crit
        )
        crit = roll >= min_crit
        
        # Calculate hit
        roll_total = roll + to_hit + roll_result.situational_bonus
        hit = roll_total >= args.target.ac
        
        # Create result
        result = AttackResultArgs(
            attack=args,
            hit=hit,
            crit=crit,
            roll=roll
        )
        
        # Log result
        if hit:
            log.record(f"Hit ({args.attack.name})", 1)
        else:
            log.record(f"Miss ({args.attack.name})", 1)
        
        if crit:
            log.record(f"Crit ({args.attack.name})", 1)
        
        # Apply attack effects
        args.attack.attack_result(result, self)
        self.events.emit("attack_result", result)
        
        # Apply all damage rolls
        for damage in result.damage_rolls:
            if crit:
                damage.dice = 2 * damage.dice
            
            self.do_damage(
                target=args.target,
                damage=damage,
                attack=args,
                spell=args.spell,
                multiplier=result.dmg_multiplier,
            )

    def attack_roll(
        self,
        attack: AttackArgs,
        to_hit: int
    ) -> AttackRollArgs:
        """
        Create attack roll with advantage/disadvantage.
        
        Args:
            attack: Attack being made
            to_hit: Base attack bonus
            
        Returns:
            AttackRollArgs with advantage/disadvantage applied
        """
        target = attack.target
        args = AttackRollArgs(attack=attack, to_hit=to_hit)
        
        # Check character conditions
        if self.poisoned:
            args.disadv = True
            
        # Check target conditions
        if target.stunned:
            args.adv = True
        
        if target.prone:
            if attack.attack.is_ranged():
                args.disadv = True
            else:
                args.adv = True
        
        if target.semistunned:
            args.adv = True
            target.semistunned = False
        
        # Allow feats to modify roll
        self.events.emit("attack_roll", args)
        
        return args

    def do_damage(
        self,
        target: "sim.target.Target",
        damage: "sim.attack.DamageRoll",
        attack: Optional["sim.events.AttackArgs"] = None,
        spell: Optional["sim.spells.Spell"] = None,
        multiplier: float = 1.0,
    ) -> None:
        """
        Apply damage to target with multipliers.
        
        Args:
            target: Target taking damage
            damage: Damage roll to apply
            attack: Attack that caused damage
            spell: Spell that caused damage
            multiplier: Damage multiplier
        """
        import sim.events
        
        args = sim.events.DamageRollArgs(
            target=target,
            damage=damage,
            attack=attack,
            spell=spell,
        )
        
        # Allow feats to modify damage
        self.events.emit("damage_roll", args)
        
        # Calculate final damage
        total_damage = math.floor(args.damage.total() * multiplier)
        
        log.record(f"Damage ({args.damage.source})", total_damage)
        
        # Apply to target
        target.apply_damage(
            damage=total_damage,
            damage_type=args.damage.damage_type,
            source=args.damage.source,
        )

    def copy(self):
        """Returns a copy of the character."""
        import copy
        return copy.deepcopy(self)

