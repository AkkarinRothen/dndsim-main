"""
Sorcerer spell implementations for D&D 5e combat simulator.

This module implements common Sorcerer spells optimized for damage output,
including signature spells like Chaos Bolt and Chromatic Orb.
"""

from typing import Optional
from util.util import cantrip_dice

from sim.spells import (
    Spell,
    TargetedSpell,
    BasicSaveSpell,
    ConcentrationSpell,
    School
)
from sim.attack import DamageRoll

import sim.target
import sim.character
import sim.event_loop


# ============================================================================
# CANTRIPS (Level 0)
# ============================================================================

class FireBolt(TargetedSpell):
    """
    Fire Bolt cantrip - ranged spell attack.
    Damage scales with character level.
    """
    def __init__(self):
        super().__init__("FireBolt", slot=0, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        num_dice = cantrip_dice(character.level)
        character.spell_attack(
            target=target,
            spell=self,
            damage=DamageRoll(source=self.name, dice=num_dice * [10]),
            is_ranged=True,
        )


class RayOfFrost(TargetedSpell):
    """
    Ray of Frost cantrip - ranged spell attack with slow effect.
    Damage scales with character level.
    """
    def __init__(self):
        super().__init__("RayOfFrost", slot=0, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        num_dice = cantrip_dice(character.level)
        character.spell_attack(
            target=target,
            spell=self,
            damage=DamageRoll(source=self.name, dice=num_dice * [8]),
            is_ranged=True,
        )


class ChillTouch(TargetedSpell):
    """
    Chill Touch cantrip - ranged spell attack.
    Damage scales with character level.
    """
    def __init__(self):
        super().__init__("ChillTouch", slot=0, school=School.NECROMANCY)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        num_dice = cantrip_dice(character.level)
        character.spell_attack(
            target=target,
            spell=self,
            damage=DamageRoll(source=self.name, dice=num_dice * [8]),
            is_ranged=True,
        )


# ============================================================================
# LEVEL 1 SPELLS
# ============================================================================

class ChromaticOrb(TargetedSpell):
    """
    Chromatic Orb - versatile damage spell.
    3d8 damage of your choice (acid, cold, fire, lightning, poison, or thunder).
    Scales with higher level slots.
    """
    def __init__(self, slot: int):
        super().__init__("ChromaticOrb", slot, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        # 3d8 + 1d8 per slot above 1st
        num_dice = 2 + self.slot
        character.spell_attack(
            target=target,
            spell=self,
            damage=DamageRoll(source=self.name, dice=num_dice * [8]),
            is_ranged=True,
        )


class MagicMissile(TargetedSpell):
    """
    Magic Missile - auto-hit force damage.
    3 darts at 1st level, +1 dart per slot level.
    Each dart does 1d4+1 damage.
    """
    def __init__(self, slot: int):
        super().__init__("MagicMissile", slot, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        num_darts = 2 + self.slot
        character.do_damage(
            target,
            damage=DamageRoll(
                source=self.name,
                dice=num_darts * [4],
                flat_dmg=num_darts,
            ),
            spell=self,
        )


class ChaosBolt(TargetedSpell):
    """
    Sorcerer signature spell - Chaos Bolt.
    2d8 + 1d6 damage with potential to chain to another target.
    Note: Chain mechanic simplified for single-target combat.
    """
    def __init__(self, slot: int):
        super().__init__("ChaosBolt", slot, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        # 2d8 + 1d6, scales with 1d6 per slot above 1st
        dice = [8, 8] + (self.slot * [6])
        character.spell_attack(
            target=target,
            spell=self,
            damage=DamageRoll(source=self.name, dice=dice),
            is_ranged=True,
        )


# ============================================================================
# LEVEL 2 SPELLS
# ============================================================================

class ScorchingRay(TargetedSpell):
    """
    Scorching Ray - multiple fire attacks.
    3 rays at 2nd level, +1 ray per slot level.
    Each ray does 2d6 damage.
    """
    def __init__(self, slot: int):
        super().__init__("ScorchingRay", slot, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        num_rays = 1 + self.slot
        for _ in range(num_rays):
            character.spell_attack(
                target=target,
                spell=self,
                damage=DamageRoll(source=self.name, dice=[6, 6]),
                is_ranged=True,
            )


# ============================================================================
# LEVEL 3 SPELLS
# ============================================================================

class Fireball(BasicSaveSpell):
    """
    Fireball - iconic AoE damage spell.
    8d6 fire damage at 3rd level, +1d6 per slot above 3rd.
    Dexterity save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "Fireball", slot, dice=(5 + slot) * [6], school=School.EVOCATION
        )


class LightningBolt(BasicSaveSpell):
    """
    Lightning Bolt - line AoE damage.
    8d6 lightning damage at 3rd level, +1d6 per slot above 3rd.
    Dexterity save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "LightningBolt", slot, dice=(5 + slot) * [6], school=School.EVOCATION
        )


# ============================================================================
# LEVEL 4 SPELLS
# ============================================================================

class Blight(BasicSaveSpell):
    """
    Blight - necrotic damage spell.
    8d8 necrotic damage at 4th level, +1d8 per slot above 4th.
    Constitution save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "Blight",
            slot,
            dice=(4 + slot) * [8],
            save_ability="con",
            school=School.NECROMANCY
        )


# ============================================================================
# LEVEL 5 SPELLS
# ============================================================================

class ConeOfCold(BasicSaveSpell):
    """
    Cone of Cold - cone AoE cold damage.
    8d8 cold damage at 5th level, +1d8 per slot above 5th.
    Constitution save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "ConeOfCold",
            slot,
            dice=(3 + slot) * [8],
            save_ability="con",
            school=School.EVOCATION
        )


# ============================================================================
# LEVEL 6 SPELLS
# ============================================================================

class ChainLightning(BasicSaveSpell):
    """
    Chain Lightning - multi-target lightning damage.
    10d8 lightning damage at 6th level, +1d8 per slot above 6th.
    Dexterity save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "ChainLightning",
            slot,
            dice=(4 + slot) * [8],
            school=School.EVOCATION
        )


class Disintegrate(TargetedSpell):
    """
    Disintegrate - single-target force damage.
    10d6 + 40 force damage at 6th level, +3d6 per slot above 6th.
    Dexterity save to avoid (no half damage).
    """
    def __init__(self, slot: int):
        super().__init__("Disintegrate", slot, school=School.TRANSMUTATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        if target.save("dex", character.spells.dc()):
            # Save negates all damage
            return
        
        # 10d6 + 40, +3d6 per slot above 6th
        num_dice = 10 + (self.slot - 6) * 3
        character.do_damage(
            target,
            damage=DamageRoll(
                source=self.name,
                dice=num_dice * [6],
                flat_dmg=40,
            ),
            spell=self,
        )


# ============================================================================
# LEVEL 7 SPELLS
# ============================================================================

class FingerOfDeath(BasicSaveSpell):
    """
    Finger of Death - single-target necrotic damage.
    7d8 + 30 necrotic damage.
    Constitution save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "FingerOfDeath",
            slot,
            dice=7 * [8],
            flat_dmg=30,
            save_ability="con",
            school=School.NECROMANCY
        )


class DelayedBlastFireball(BasicSaveSpell):
    """
    Delayed Blast Fireball - enhanced fireball.
    12d6 fire damage at 7th level, +1d6 per slot above 7th.
    Dexterity save for half damage.
    (Delay mechanic simplified for immediate damage)
    """
    def __init__(self, slot: int):
        super().__init__(
            "DelayedBlastFireball",
            slot,
            dice=(5 + slot) * [6],
            school=School.EVOCATION
        )


# ============================================================================
# LEVEL 8 SPELLS
# ============================================================================

class Sunburst(BasicSaveSpell):
    """
    Sunburst - radiant AoE damage.
    12d6 radiant damage.
    Constitution save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "Sunburst",
            slot,
            dice=12 * [6],
            save_ability="con",
            school=School.EVOCATION
        )


# ============================================================================
# LEVEL 9 SPELLS
# ============================================================================

class MeteorSwarm(BasicSaveSpell):
    """
    Meteor Swarm - ultimate AoE destruction.
    40d6 fire and bludgeoning damage.
    Dexterity save for half damage.
    """
    def __init__(self, slot: int):
        super().__init__(
            "MeteorSwarm",
            slot,
            dice=40 * [6],
            school=School.EVOCATION
        )
        assert slot == 9
