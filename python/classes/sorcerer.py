"""
Sorcerer class implementation for D&D 5e combat simulator.

This module implements Sorcerer class features including Metamagic,
Font of Magic (Sorcery Points), and the Draconic Bloodline subclass.

COMPLETE SELF-CONTAINED VERSION - All spells included inline.
"""

from typing import List, Literal, Optional
from enum import IntEnum

from util.util import apply_asi_feats, cantrip_dice
from sim.spells import (
    Spell,
    Spellcaster,
    TargetedSpell,
    BasicSaveSpell,
    School,
)
from sim.attack import DamageRoll
from feats import ASI

import sim.character
import sim.spells
import sim.feat
import sim.target
import sim.core_feats


# ============================================================================
# SORCERER SPELL IMPLEMENTATIONS
# ============================================================================

# --- CANTRIPS ---

class FireBolt(TargetedSpell):
    """Fire Bolt cantrip - ranged spell attack."""
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


# --- LEVEL 1 SPELLS ---

class ChromaticOrb(TargetedSpell):
    """Chromatic Orb - 3d8 damage, scales with slot."""
    def __init__(self, slot: int):
        super().__init__("ChromaticOrb", slot, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        num_dice = 2 + self.slot
        character.spell_attack(
            target=target,
            spell=self,
            damage=DamageRoll(source=self.name, dice=num_dice * [8]),
            is_ranged=True,
        )


class MagicMissile(TargetedSpell):
    """Magic Missile - auto-hit force damage."""
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
    """Chaos Bolt - Sorcerer signature spell."""
    def __init__(self, slot: int):
        super().__init__("ChaosBolt", slot, school=School.EVOCATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        dice = [8, 8] + (self.slot * [6])
        character.spell_attack(
            target=target,
            spell=self,
            damage=DamageRoll(source=self.name, dice=dice),
            is_ranged=True,
        )


# --- LEVEL 2 SPELLS ---

class ScorchingRay(TargetedSpell):
    """Scorching Ray - multiple fire attacks."""
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


# --- LEVEL 3 SPELLS ---

class Fireball(BasicSaveSpell):
    """Fireball - iconic AoE damage."""
    def __init__(self, slot: int):
        super().__init__(
            "Fireball", slot, dice=(5 + slot) * [6], save_ability="dex", school=School.EVOCATION
        )


class LightningBolt(BasicSaveSpell):
    """Lightning Bolt - line AoE damage."""
    def __init__(self, slot: int):
        super().__init__(
            "LightningBolt", slot, dice=(5 + slot) * [6], save_ability="dex", school=School.EVOCATION
        )


# --- LEVEL 4 SPELLS ---

class Blight(BasicSaveSpell):
    """Blight - necrotic damage."""
    def __init__(self, slot: int):
        super().__init__(
            "Blight",
            slot,
            dice=(4 + slot) * [8],
            save_ability="con",
            school=School.NECROMANCY
        )


# --- LEVEL 5 SPELLS ---

class ConeOfCold(BasicSaveSpell):
    """Cone of Cold - cone AoE cold damage."""
    def __init__(self, slot: int):
        super().__init__(
            "ConeOfCold",
            slot,
            dice=(3 + slot) * [8],
            save_ability="con",
            school=School.EVOCATION
        )


# --- LEVEL 6 SPELLS ---

class ChainLightning(BasicSaveSpell):
    """Chain Lightning - multi-target lightning damage."""
    def __init__(self, slot: int):
        super().__init__(
            "ChainLightning",
            slot,
            dice=(4 + slot) * [8],
            save_ability="dex",
            school=School.EVOCATION
        )


class Disintegrate(TargetedSpell):
    """Disintegrate - single-target force damage."""
    def __init__(self, slot: int):
        super().__init__("Disintegrate", slot, school=School.TRANSMUTATION)

    def cast_target(
        self, character: "sim.character.Character", target: "sim.target.Target"
    ):
        if target.save("dex", character.spells.dc()):
            return
        
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


# --- LEVEL 7 SPELLS ---

class FingerOfDeath(BasicSaveSpell):
    """Finger of Death - single-target necrotic damage."""
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
    """Delayed Blast Fireball - enhanced fireball."""
    def __init__(self, slot: int):
        super().__init__(
            "DelayedBlastFireball",
            slot,
            dice=(5 + slot) * [6],
            save_ability="dex",
            school=School.EVOCATION
        )


# --- LEVEL 8 SPELLS ---

class Sunburst(BasicSaveSpell):
    """Sunburst - radiant AoE damage."""
    def __init__(self, slot: int):
        super().__init__(
            "Sunburst",
            slot,
            dice=12 * [6],
            save_ability="con",
            school=School.EVOCATION
        )


# --- LEVEL 9 SPELLS ---

class MeteorSwarm(BasicSaveSpell):
    """Meteor Swarm - ultimate AoE destruction."""
    def __init__(self, slot: int):
        super().__init__(
            "MeteorSwarm",
            slot,
            dice=40 * [6],
            save_ability="dex",
            school=School.EVOCATION
        )
        assert slot == 9


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

Metamagic = Literal[
    "Quickened",
    "Twinned",
    "Empowered",
    "Heightened",
    "Subtle",
    "Extended",
    "Distant",
    "Careful",
]


# ============================================================================
# CONSTANTS
# ============================================================================

class SorcererLevels(IntEnum):
    """Key level milestones for Sorcerer class features."""
    INNATE_SORCERY = 1
    FONT_OF_MAGIC = 2
    METAMAGIC_1 = 2
    SORCEROUS_RESTORATION = 5
    METAMAGIC_2 = 10
    METAMAGIC_3 = 17
    ARCANE_APOTHEOSIS = 20


class DraconicLevels(IntEnum):
    """Key level milestones for Draconic Bloodline subclass."""
    DRACONIC_RESILIENCE = 3
    ELEMENTAL_AFFINITY = 6


DEFAULT_SORCERER_STATS = [10, 10, 14, 10, 10, 17]


# ============================================================================
# CORE SORCERER FEATURES
# ============================================================================

class SorcererLevel(sim.core_feats.ClassLevels):
    """Sorcerer class levels and full spellcasting progression."""
    
    def __init__(self, level: int):
        super().__init__(
            name="Sorcerer",
            level=level,
            spellcaster=Spellcaster.FULL
        )


class InnateSorcery(sim.feat.Feat):
    """Level 1 Sorcerer feature: Innate Sorcery."""
    
    def __init__(self):
        super().__init__()
        self.active: bool = False
        self.duration: int = 0

    def apply(self, character: "sim.character.Character") -> None:
        super().apply(character)
        character.add_resource('Innate Sorcery', max_uses=character.prof, short_rest=False)

    def long_rest(self) -> None:
        self.active = False
        self.duration = 0

    def begin_turn(self, target: "sim.target.Target") -> None:
        if self.active:
            self.duration -= 1
            if self.duration <= 0:
                self.active = False


class SorceryPointsResource(sim.feat.Feat):
    """Level 2 Sorcerer feature: Font of Magic."""
    
    def __init__(self, level: int):
        super().__init__()
        self.level: int = level

    def apply(self, character: "sim.character.Character") -> None:
        super().apply(character)
        character.add_resource('Sorcery Points', max_uses=self.level, short_rest=False)


class Metamagics(sim.feat.Feat):
    """Level 2 Sorcerer feature: Metamagic."""
    
    def __init__(self, metamagics: List[Metamagic]):
        super().__init__()
        self.metamagics: List[Metamagic] = metamagics


class SorcerousRestoration(sim.feat.Feat):
    """Level 5 Sorcerer feature: Sorcerous Restoration."""
    
    POINTS_RESTORED = 4
    
    def __init__(self):
        super().__init__()

    def short_rest(self) -> None:
        if 'Sorcery Points' in self.character.resources:
            self.character.resources['Sorcery Points'].gain(self.POINTS_RESTORED, detail="Sorcerous Restoration")


class ArcaneApotheosis(sim.feat.Feat):
    """Level 20 Sorcerer feature: Arcane Apotheosis."""
    
    def __init__(self):
        super().__init__()


# ============================================================================
# DRACONIC BLOODLINE FEATURES
# ============================================================================

class DraconicResilience(sim.feat.Feat):
    """Draconic Bloodline Level 3 feature: Draconic Resilience."""
    
    def __init__(self):
        super().__init__()


class ElementalAffinity(sim.feat.Feat):
    """Draconic Bloodline Level 6 feature: Elemental Affinity."""
    
    def __init__(self):
        super().__init__()
        self.used_this_spell: bool = False

    def begin_turn(self, target: "sim.target.Target") -> None:
        self.used_this_spell = False

    def damage_roll(self, args) -> None:
        if (
            args.spell
            and not self.used_this_spell
            and args.spell.name in [
                "FireBolt", "Fireball", "ScorchingRay", 
                "DelayedBlastFireball", "MeteorSwarm"
            ]
        ):
            self.used_this_spell = True
            args.damage.flat_dmg += self.character.mod("cha")


# ============================================================================
# COMBAT ACTION
# ============================================================================

class SorcererAction(sim.feat.Feat):
    """Automated Sorcerer spell selection for optimal DPR."""
    
    def action(self, target: "sim.target.Target") -> None:
        slot = self.character.spells.highest_slot()
        spell: Optional["sim.spells.Spell"] = None
        
        if slot >= 9:
            spell = MeteorSwarm(slot)
        elif slot >= 8:
            spell = Sunburst(slot)
        elif slot >= 7:
            spell = FingerOfDeath(slot)
        elif slot >= 6:
            spell = Disintegrate(slot)
        elif slot >= 5:
            spell = ConeOfCold(slot)
        elif slot >= 4:
            spell = Blight(slot)
        elif slot >= 3:
            spell = Fireball(slot)
        elif slot >= 2:
            spell = ScorchingRay(slot)
        elif slot >= 1:
            if self.character.level >= 3:
                spell = ChaosBolt(slot)
            else:
                spell = ChromaticOrb(slot)
        else:
            spell = FireBolt()
        
        if spell is not None:
            self.character.spells.cast(spell, target)


# ============================================================================
# FEAT BUILDERS
# ============================================================================

def sorcerer_feats(
    level: int,
    metamagics: List[Metamagic],
    asis: Optional[List["sim.feat.Feat"]] = None
) -> List["sim.feat.Feat"]:
    """Build the standard Sorcerer feat list for a given level."""
    feats: List["sim.feat.Feat"] = []
    
    if level >= 1:
        feats.append(SorcererLevel(level))
        feats.append(InnateSorcery())
    
    if level >= SorcererLevels.FONT_OF_MAGIC:
        feats.append(SorceryPointsResource(level))
        feats.append(Metamagics(metamagics))
    
    if level >= SorcererLevels.SORCEROUS_RESTORATION:
        feats.append(SorcerousRestoration())
    
    if level >= SorcererLevels.ARCANE_APOTHEOSIS:
        feats.append(ArcaneApotheosis())
    
    apply_asi_feats(level=level, feats=feats, asis=asis)
    
    return feats


def draconic_sorcerer_feats(level: int) -> List["sim.feat.Feat"]:
    """Build Draconic Bloodline subclass feat list."""
    feats: List["sim.feat.Feat"] = []
    
    if level >= DraconicLevels.DRACONIC_RESILIENCE:
        feats.append(DraconicResilience())
    
    if level >= DraconicLevels.ELEMENTAL_AFFINITY:
        feats.append(ElementalAffinity())
    
    return feats


# ============================================================================
# CHARACTER CLASS
# ============================================================================

class DraconicSorcerer(sim.character.Character):
    """
    Draconic Bloodline Sorcerer with complete combat logic.
    
    A fire-focused spellcaster who channels draconic power for
    devastating magical attacks.
    """
    
    def __init__(self, level: int, **kwargs) -> None:
        """
        Initialize Draconic Bloodline Sorcerer.
        
        Args:
            level: Character level (1-20)
        """
        feats: List["sim.feat.Feat"] = []
        
        # Add intelligent spell selection
        feats.append(SorcererAction())
        
        # Build Sorcerer progression
        metamagic_choices: List[Metamagic] = ["Empowered", "Heightened"]
        if level >= SorcererLevels.METAMAGIC_2:
            metamagic_choices.extend(["Quickened", "Twinned"])
        if level >= SorcererLevels.METAMAGIC_3:
            metamagic_choices.extend(["Careful", "Extended"])
        
        feats.extend(
            sorcerer_feats(
                level,
                metamagics=metamagic_choices,
                asis=[
                    ASI(["cha"]),
                    ASI(["cha"]),
                    ASI(["con"]),
                    ASI(["dex"]),
                    ASI(["con", "dex"]),
                ],
            )
        )
        
        # Add Draconic Bloodline features
        feats.extend(draconic_sorcerer_feats(level))
        
        # Initialize character
        super().__init__(
            name="Draconic Sorcerer",  # ✅ Explicit name
            level=level,
            stats=DEFAULT_SORCERER_STATS,
            base_feats=feats,
            spell_mod="cha",
        )
