"""
Combat Presets - Pre-configured combat scenarios for quick testing.

This module defines a collection of ready-to-use combat encounters with
balanced party compositions and enemy configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class CombatPreset:
    """
    A pre-configured combat scenario.
    
    Attributes:
        name: Display name of the preset
        party: List of character keys to include in the party
        enemies: List of (monster_name, count) tuples
        level: Party level
        description: Detailed description of the scenario
    """
    name: str
    party: List[str]
    enemies: List[Tuple[str, int]]
    level: int
    description: str


# Preset combat scenarios
COMBAT_PRESETS: Dict[str, CombatPreset] = {
    "tutorial": CombatPreset(
        name="Tutorial: Party of Four vs. Goblins",
        party=["fighter", "wizard", "rogue", "cleric"],
        enemies=[("goblin", 4)],
        level=1,
        description=(
            "A basic combat encounter perfect for learning the simulator controls. "
            "A balanced level 1 party faces a group of goblins in a straightforward fight."
        )
    ),
    
    "orc_raid": CombatPreset(
        name="Orc Raid: Defend the Village",
        party=["fighter", "fighter", "cleric", "wizard"],
        enemies=[("orc", 2), ("goblin", 2)],
        level=3,
        description=(
            "Defend against a small but fierce raiding party. "
            "Two orcs lead their goblin minions in an assault on a village. "
            "Your martial-heavy party must hold the line."
        )
    ),
    
    "kobold_ambush": CombatPreset(
        name="Kobold Ambush: Tunnel Trap",
        party=["ranger", "rogue", "cleric"],
        enemies=[("kobold", 6)],
        level=2,
        description=(
            "A small party ventures into kobold-infested tunnels. "
            "The kobolds use their numbers and pack tactics to overwhelm intruders. "
            "Quick thinking and tactical positioning are essential."
        )
    ),
    
    "bandit_encounter": CombatPreset(
        name="Highway Robbery: Bandit Ambush",
        party=["fighter", "wizard", "rogue"],
        enemies=[("bandit", 3), ("bandit captain", 1)],
        level=4,
        description=(
            "Bandits have set up an ambush on the road. "
            "Their captain is a cunning tactician who coordinates the assault. "
            "Can your party overcome superior numbers and tactics?"
        )
    ),
    
    "undead_crypt": CombatPreset(
        name="Crypt Crawl: Skeleton Warriors",
        party=["paladin", "cleric", "fighter"],
        enemies=[("skeleton", 4), ("zombie", 2)],
        level=2,
        description=(
            "The dead walk in an ancient crypt. "
            "Skeletons and zombies rise to defend their tomb from intruders. "
            "Your holy warriors must cleanse this unhallowed ground."
        )
    ),
    
    # Uncomment when high-CR monsters are available
    # "boss_fight": CombatPreset(
    #     name="Boss Fight: The Lair of the Dragon",
    #     party=["paladin", "wizard", "cleric", "ranger"],
    #     enemies=[("adult_red_dragon", 1)],
    #     level=10,
    #     description=(
    #         "An epic confrontation with an adult red dragon in its lair. "
    #         "This legendary creature possesses devastating breath weapons, "
    #         "powerful melee attacks, and frightful presence. "
    #         "Only a well-coordinated high-level party stands a chance."
    #     )
    # ),
}


def get_preset(preset_key: str) -> CombatPreset | None:
    """
    Get a combat preset by its key.
    
    Args:
        preset_key: The preset identifier
    
    Returns:
        CombatPreset if found, None otherwise
    """
    return COMBAT_PRESETS.get(preset_key)


def list_presets() -> List[Tuple[str, str]]:
    """
    Get a list of all available presets.
    
    Returns:
        List of (key, name) tuples
    """
    return [(key, preset.name) for key, preset in COMBAT_PRESETS.items()]


def get_preset_by_level(level: int) -> List[Tuple[str, CombatPreset]]:
    """
    Get presets suitable for a given party level.
    
    Args:
        level: Party level
    
    Returns:
        List of (key, preset) tuples for presets at or near the given level
    """
    suitable_presets = []
    
    for key, preset in COMBAT_PRESETS.items():
        # Include presets within 2 levels
        if abs(preset.level - level) <= 2:
            suitable_presets.append((key, preset))
    
    # Sort by level difference
    suitable_presets.sort(key=lambda x: abs(x[1].level - level))
    
    return suitable_presets


def validate_preset(preset: CombatPreset) -> Tuple[bool, str]:
    """
    Validate a combat preset for common issues.
    
    Args:
        preset: The preset to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not preset.party:
        return False, "Preset has no party members"
    
    if not preset.enemies:
        return False, "Preset has no enemies"
    
    if not 1 <= preset.level <= 20:
        return False, f"Invalid level: {preset.level}"
    
    total_enemies = sum(count for _, count in preset.enemies)
    if total_enemies == 0:
        return False, "Total enemy count is zero"
    
    if total_enemies > 20:
        return False, f"Too many enemies: {total_enemies}"
    
    if len(preset.party) > 10:
        return False, f"Too many party members: {len(preset.party)}"
    
    return True, ""


# Validate all presets on module load
def _validate_all_presets():
    """Validate all presets and log warnings for invalid ones."""
    import logging
    logger = logging.getLogger(__name__)
    
    for key, preset in COMBAT_PRESETS.items():
        is_valid, error = validate_preset(preset)
        if not is_valid:
            logger.warning(f"Invalid preset '{key}': {error}")


# Run validation
_validate_all_presets()