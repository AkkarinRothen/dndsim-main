"""
Warlock class implementation for D&D 5e combat simulator.

This module implements Warlock class features including Pact Magic, Eldritch Invocations,
Mystic Arcanum, and the Fiend patron.

FIXED ISSUES:
- Removed duplicate super().__init__() calls
- Proper initialization pattern
- Clear Pact Magic vs Mystic Arcanum distinction
- Correct resource management
"""

from typing import List, Optional

from feats import ASI
from sim.character import Character
from sim.events import AttackResultArgs
from sim.target import Target
from spells.summons import SummonFey, SummonFiend
from spells.warlock import EldritchBlast
from spells.wizard import Blight, FingerOfDeath, Fireball
from util.util import apply_asi_feats, apply_feats_at_levels

import sim.core_feats
import sim.feat


# ============================================================================
# CORE WARLOCK FEATURES
# ============================================================================

class WarlockLevel(sim.core_feats.ClassLevels):
    """
    Represents Warlock class levels and Pact Magic progression.
    
    Warlocks use Pact Magic instead of standard Spellcasting.
    They have fewer spell slots that recharge on short rest.
    """
    
    def __init__(self, level: int):
        """
        Initialize Warlock class levels.
        
        Args:
            level: Character level (1-20)
        """
        super().__init__(name="Warlock", level=level)

    def apply(self, character: Character) -> None:
        """
        Apply Warlock levels and Pact Magic slots.
        
        Args:
            character: The character to apply Warlock levels to
        """
        super().apply(character)
        character.spells.add_pact_spellcaster_level(self.level)


class MysticArcanum(sim.feat.Feat):
    """
    High-level Warlock feature: Mystic Arcanum.
    
    At levels 11, 13, 15, and 17, you learn a powerful spell
    that you can cast once per long rest without using a spell slot.
    
    This represents mastery over specific high-level magic.
    """
    
    def __init__(self, spell_name: str):
        """
        Initialize Mystic Arcanum.
        
        Args:
            spell_name: Name of the spell (used as resource identifier)
        """
        super().__init__()
        self.spell_name: str = spell_name

    def apply(self, character: Character) -> None:
        """
        Add Mystic Arcanum resource to character.
        
        Args:
            character: The character to apply this to
        """
        super().apply(character)
        character.add_resource(self.spell_name, max_uses=1, short_rest=False)


# ============================================================================
# ELDRITCH INVOCATIONS
# ============================================================================

class AgonizingBlast(sim.feat.Feat):
    """
    Eldritch Invocation: Agonizing Blast.
    
    Add your Charisma modifier to Eldritch Blast damage.
    This dramatically increases the damage of your signature cantrip.
    """
    
    def attack_result(self, args: AttackResultArgs) -> None:
        """
        Add Charisma modifier to Eldritch Blast damage.
        
        Args:
            args: Attack result arguments
        """
        if (
            args.hits()
            and args.attack.spell is not None
            and args.attack.spell.name == "EldritchBlast"
        ):
            args.add_damage(
                source="Agonizing Blast",
                damage=self.character.mod("cha")
            )


# ============================================================================
# FEAT BUILDERS
# ============================================================================

def warlock_feats(
    level: int,
    invocations: Optional[list["sim.feat.Feat"]] = None,
    asis: Optional[list["sim.feat.Feat"]] = None,
    arcanums: Optional[list[str]] = None,
) -> list["sim.feat.Feat"]:
    """
    Build the standard Warlock feat list for a given level.
    
    Args:
        level: Character level (1-20)
        invocations: Eldritch Invocations known
        asis: ASI/feat choices at appropriate levels
        arcanums: Mystic Arcanum spell names (levels 11, 13, 15, 17)
        
    Returns:
        List of Warlock class feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 1: Class basics
    if level >= 1:
        feats.append(WarlockLevel(level))
    
    # Level 2: Magical Cunning (TODO: short rest spell recovery)
    # Level 9: Contact Patron (utility, not relevant)
    
    # Mystic Arcanum at levels 11, 13, 15, 17
    if arcanums is None:
        arcanums = [
            "SummonFiend",      # 6th level (gained at 11)
            "FingerOfDeath",    # 7th level (gained at 13)
            "Befuddlement",     # 8th level (gained at 15)
            "PowerWordKill",    # 9th level (gained at 17)
        ]
    
    if level >= 11:
        feats.append(MysticArcanum(arcanums[0]))
    if level >= 13:
        feats.append(MysticArcanum(arcanums[1]))
    if level >= 15:
        feats.append(MysticArcanum(arcanums[2]))
    if level >= 17:
        feats.append(MysticArcanum(arcanums[3]))
    
    # Level 20: Eldritch Master (TODO: spell slot recovery)
    
    # Apply ASIs/Feats
    apply_asi_feats(level, feats, asis)
    
    # Apply Invocations at appropriate levels
    # Warlocks gain invocations at levels: 1, 2, 2, 5, 5, 7, 9, 12, 15, 18
    if invocations:
        apply_feats_at_levels(
            level,
            feats,
            schedule=[1, 2, 2, 5, 5, 7, 9, 12, 15, 18],
            new_feats=invocations,
        )
    
    return feats


def fiend_warlock_feats(level: int) -> List["sim.feat.Feat"]:
    """
    Build Fiend patron feat list.
    
    Args:
        level: Character level (3-20)
        
    Returns:
        List of Fiend patron feats
    """
    feats: List["sim.feat.Feat"] = []
    
    # Level 3: Dark One's Blessing (temp HP on kill, not relevant)
    # Level 6: Dark One's Own Luck (reroll ability check, not relevant)
    # Level 10: Fiendish Resilience (resistance, defensive)
    # Level 14: Hurl Through Hell (TODO: implementation)
    
    return feats


# ============================================================================
# COMBAT ACTIONS
# ============================================================================

class FiendWarlockAction(sim.feat.Feat):
    """
    Automated Fiend Warlock spell selection for optimal DPR.
    
    Priority:
    1. Summon Fiend (Mystic Arcanum) if not concentrating
    2. Finger of Death (Mystic Arcanum) for burst
    3. Summon Fey with Pact slots if not concentrating
    4. Blight for high-level damage
    5. Fireball for mid-level damage
    6. Eldritch Blast as fallback
    """
    
    def action(self, target: Target) -> None:
        """
        Choose and cast the optimal spell for the current situation.
        
        Args:
            target: The target to attack/affect
        """
        # Check for Mystic Arcanum: Summon Fiend (6th level)
        if (
            self.character.has_resource("SummonFiend")
            and not self.character.spells.is_concentrating()
        ):
            self.character.resources["SummonFiend"].use(detail="Mystic Arcanum: Summon Fiend", target=target)
            self.character.spells.cast(
                SummonFiend(slot=6),
                target=target,
                ignore_slot=True  # Mystic Arcanum doesn't use slots
            )
            return
        
        # Check for Mystic Arcanum: Finger of Death (7th level)
        if self.character.has_resource("FingerOfDeath"):
            self.character.resources["FingerOfDeath"].use(detail="Mystic Arcanum: Finger of Death", target=target)
            self.character.spells.cast(
                FingerOfDeath(slot=7),
                target=target,
                ignore_slot=True
            )
            return
        
        # Use Pact Magic slots
        slot = self.character.spells.highest_slot()
        
        # Summon Fey if not concentrating
        if slot >= 4 and not self.character.spells.is_concentrating():
            self.character.spells.cast(SummonFey(slot), target=target)
            return
        
        # High-level damage spells
        if slot >= 5:
            self.character.spells.cast(Blight(slot), target=target)
            return
        
        if slot >= 3:
            self.character.spells.cast(Fireball(slot), target=target)
            return
        
        # Fallback to Eldritch Blast
        self.character.spells.cast(EldritchBlast(), target=target)


# ============================================================================
# CHARACTER CLASS
# ============================================================================

class FiendWarlock(sim.character.Character):
    """
    Fiend Patron Warlock.
    
    A spellcaster who made a pact with a powerful fiend for magical power.
    Uses Pact Magic (few slots that recharge on short rest) and Eldritch Blast.
    
    The Fiend Warlock excels at:
    - Consistent damage with Agonizing Blast
    - Flexible short rest spellcasting
    - High-level spell access via Mystic Arcanum
    - Summoning powerful fiendish allies
    
    Combat Strategy:
    - Summons Fiend/Fey for sustained damage
    - Uses Mystic Arcanum for big damage spells
    - Blasts with Eldritch Blast when slots exhausted
    - Recovers slots on short rest for sustained combat
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Fiend Warlock.
        
        Args:
            level: Character level (1-20)
            **kwargs: Additional character initialization arguments
        """
        # Build feat list
        feats: List["sim.feat.Feat"] = []
        
        # Standard Warlock progression
        feats.extend(
            warlock_feats(
                level,
                asis=[
                    ASI(["cha"]),           # Boost primary stat
                    ASI(["cha", "dex"]),    # Max Charisma, boost AC
                ],
                invocations=[
                    AgonizingBlast(),       # Essential for damage
                    # More invocations could be added here
                ],
                arcanums=[
                    "SummonFiend",          # 6th level (level 11)
                    "FingerOfDeath",        # 7th level (level 13)
                    "Befuddlement",         # 8th level (level 15)
                    "PowerWordKill",        # 9th level (level 17)
                ],
            )
        )
        
        # Fiend patron features
        feats.extend(fiend_warlock_feats(level))
        
        # Combat action
        feats.append(FiendWarlockAction())
        
        # Initialize character
        # Stats: Charisma for spellcasting
        super().__init__(
            name="Fiend Warlock",  # ✅ Explicit name
            level=level,
            stats=[10, 10, 10, 10, 10, 17],  # Cha-focused
            base_feats=feats,
            spell_mod="cha",  # Charisma-based spellcasting
            ac=13,  # Base AC (could wear light armor)
        )


# ============================================================================
# ALTERNATIVE PATRONS (TODO)
# ============================================================================

class ArchfeyWarlock(sim.character.Character):
    """
    Archfey Patron Warlock (placeholder for future implementation).
    
    Focus on charm, illusion, and fey magic.
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Archfey Warlock.
        
        Args:
            level: Character level (1-20)
            **kwargs: Additional character initialization arguments
        """
        # Similar to FiendWarlock but with different patron features
        feats: List["sim.feat.Feat"] = []
        
        feats.extend(
            warlock_feats(
                level,
                asis=[ASI(["cha"]), ASI(["cha", "dex"])],
                invocations=[AgonizingBlast()],
            )
        )
        
        # Add Archfey-specific action
        feats.append(FiendWarlockAction())  # Reuse for now
        
        super().__init__(
            name="Archfey Warlock",
            level=level,
            stats=[10, 10, 10, 10, 10, 17],
            base_feats=feats,
            spell_mod="cha",
            ac=13,
        )


class GreatOldOneWarlock(sim.character.Character):
    """
    Great Old One Patron Warlock (placeholder for future implementation).
    
    Focus on psychic damage and mind control.
    """
    
    def __init__(self, level: int, **kwargs):
        """
        Initialize Great Old One Warlock.
        
        Args:
            level: Character level (1-20)
            **kwargs: Additional character initialization arguments
        """
        feats: List["sim.feat.Feat"] = []
        
        feats.extend(
            warlock_feats(
                level,
                asis=[ASI(["cha"]), ASI(["cha", "dex"])],
                invocations=[AgonizingBlast()],
            )
        )
        
        feats.append(FiendWarlockAction())  # Reuse for now
        
        super().__init__(
            name="Great Old One Warlock",
            level=level,
            stats=[10, 10, 10, 10, 10, 17],
            base_feats=feats,
            spell_mod="cha",
            ac=13,
        )
