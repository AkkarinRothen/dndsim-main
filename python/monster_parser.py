"""
Monster Parser - Dynamically creates monster classes from 5etools JSON data.

This module parses monster stat blocks from the 5etools bestiary format and
generates Python classes that can be instantiated for combat simulations.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union

from sim.monster import BaseMonster

logger = logging.getLogger(__name__)


# CR to Proficiency Bonus mapping (D&D 5e rules)
CR_PROFICIENCY_MAP: Dict[str, int] = {
    '0': 2, '1/8': 2, '1/4': 2, '1/2': 2,
    '1': 2, '2': 2, '3': 2, '4': 2,
    '5': 3, '6': 3, '7': 3, '8': 3,
    '9': 4, '10': 4, '11': 4, '12': 4,
    '13': 5, '14': 5, '15': 5, '16': 5,
    '17': 6, '18': 6, '19': 6, '20': 6,
    '21': 7, '22': 7, '23': 7, '24': 7,
    '25': 8, '26': 8, '27': 8, '28': 8,
    '29': 9, '30': 9
}

DEFAULT_PROFICIENCY_BONUS = 2
DEFAULT_ABILITY_SCORE = 10


def cr_to_prof_bonus(cr_value: Union[str, int, float]) -> int:
    """
    Convert a Challenge Rating to a proficiency bonus.
    
    Args:
        cr_value: CR as string (e.g., '1/4', '5') or numeric value
    
    Returns:
        Proficiency bonus for the given CR
    
    Examples:
        >>> cr_to_prof_bonus('1/4')
        2
        >>> cr_to_prof_bonus('10')
        4
        >>> cr_to_prof_bonus(5)
        3
    """
    cr_str = str(cr_value)
    return CR_PROFICIENCY_MAP.get(cr_str, DEFAULT_PROFICIENCY_BONUS)


def parse_armor_class(ac_data: Union[int, List, Dict]) -> int:
    """
    Parse armor class from various 5etools formats.
    
    Args:
        ac_data: AC value in various possible formats
    
    Returns:
        AC as integer
    
    Raises:
        ValueError: If AC cannot be parsed
    """
    if isinstance(ac_data, int):
        return ac_data
    
    if isinstance(ac_data, list):
        if not ac_data:
            raise ValueError("AC list is empty")
        
        first_entry = ac_data[0]
        
        if isinstance(first_entry, int):
            return first_entry
        
        if isinstance(first_entry, dict) and 'ac' in first_entry:
            return int(first_entry['ac'])
    
    if isinstance(ac_data, dict) and 'ac' in ac_data:
        return int(ac_data['ac'])
    
    raise ValueError(f"Unable to parse AC from: {ac_data}")


def parse_hit_points(hp_data: Dict[str, Any]) -> int:
    """
    Parse hit points from 5etools HP data.
    
    Args:
        hp_data: HP dictionary with 'average', 'formula', etc.
    
    Returns:
        Average HP as integer
    
    Raises:
        ValueError: If HP cannot be parsed
    """
    if not isinstance(hp_data, dict):
        raise ValueError(f"HP data must be a dictionary, got {type(hp_data)}")
    
    if 'average' in hp_data:
        return int(hp_data['average'])
    
    if 'special' in hp_data:
        # Some monsters have special HP rules
        logger.warning(f"Monster has special HP rules: {hp_data['special']}")
        return 50  # Default for special cases
    
    raise ValueError(f"Unable to parse HP from: {hp_data}")


def sanitize_class_name(name: str) -> str:
    """
    Convert a monster name to a valid Python class name.
    
    Args:
        name: Monster name
    
    Returns:
        Valid Python identifier
    
    Examples:
        >>> sanitize_class_name("Adult Red Dragon")
        'AdultRedDragon'
        >>> sanitize_class_name("Goblin Boss (Elite)")
        'GoblinBossElite'
    """
    # Remove special characters and join words
    sanitized = "".join(c for c in name if c.isalnum() or c.isspace())
    
    # Convert to PascalCase
    words = sanitized.split()
    class_name = "".join(word.capitalize() for word in words)
    
    # Ensure it starts with a letter
    if not class_name or not class_name[0].isalpha():
        class_name = "Monster" + class_name
    
    return class_name


def parse_resistance_list(data: Union[List, str, None]) -> List[str]:
    """
    Parse damage resistances, vulnerabilities, or immunities.
    
    Args:
        data: Resistance data in various formats
    
    Returns:
        List of damage type strings
    """
    if data is None:
        return []
    
    if isinstance(data, str):
        return [data]
    
    if isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # Complex resistance (e.g., "resistant to X except from Y")
                if 'resist' in item:
                    result.extend(parse_resistance_list(item['resist']))
        return result
    
    return []


def create_monster_class(monster_data: Dict[str, Any]) -> Optional[type[BaseMonster]]:
    """
    Dynamically create a monster class from 5etools JSON data.
    
    Args:
        monster_data: Dictionary containing monster statistics
    
    Returns:
        Monster class or None if parsing fails
    
    Note:
        The created class is automatically added to the module namespace
        to support pickling.
    """
    try:
        # Extract basic information
        name = monster_data.get('name')
        if not name:
            logger.warning("Monster missing name, skipping")
            return None
        
        # Parse AC
        ac_data = monster_data.get('ac')
        if not ac_data:
            logger.warning(f"Monster '{name}' missing AC, skipping")
            return None
        ac = parse_armor_class(ac_data)
        
        # Parse HP
        hp_data = monster_data.get('hp')
        if not hp_data:
            logger.warning(f"Monster '{name}' missing HP, skipping")
            return None
        hp = parse_hit_points(hp_data)
        
        # Get proficiency bonus from CR
        cr = monster_data.get('cr', '0')
        prof_bonus = cr_to_prof_bonus(cr)
        
        # Get ability scores
        str_score = monster_data.get('str', DEFAULT_ABILITY_SCORE)
        dex_score = monster_data.get('dex', DEFAULT_ABILITY_SCORE)
        con_score = monster_data.get('con', DEFAULT_ABILITY_SCORE)
        int_score = monster_data.get('int', DEFAULT_ABILITY_SCORE)
        wis_score = monster_data.get('wis', DEFAULT_ABILITY_SCORE)
        cha_score = monster_data.get('cha', DEFAULT_ABILITY_SCORE)
        
        # Parse resistances, vulnerabilities, immunities
        resistances = parse_resistance_list(monster_data.get('resist'))
        vulnerabilities = parse_resistance_list(monster_data.get('vulnerable'))
        immunities = parse_resistance_list(monster_data.get('immune'))
        
        # Create __init__ method
        def monster_init(self):
            BaseMonster.__init__(
                self,
                name, ac, hp,
                str_score, dex_score, con_score,
                int_score, wis_score, cha_score,
                prof_bonus,
                resistances=resistances,
                vulnerabilities=vulnerabilities,
                immunities=immunities
            )
        
        # Generate class name
        class_name = sanitize_class_name(name)
        
        # Create the class dynamically
        monster_class = type(class_name, (BaseMonster,), {"__init__": monster_init})
        
        # Add to module namespace for pickling support
        current_module = sys.modules[__name__]
        setattr(current_module, class_name, monster_class)
        
        logger.debug(f"Created monster class: {class_name} (CR {cr}, AC {ac}, HP {hp})")
        
        return monster_class
        
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(
            f"Failed to parse monster '{monster_data.get('name', 'Unknown')}': {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error parsing monster '{monster_data.get('name', 'Unknown')}': {e}",
            exc_info=True
        )
        return None


def load_monsters_from_json(file_path: str) -> Dict[str, type[BaseMonster]]:
    """
    Load all monsters from a 5etools bestiary JSON file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        Dictionary mapping monster keys to monster classes
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    logger.info(f"Loading monsters from: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    monsters: Dict[str, type[BaseMonster]] = {}
    monster_list = data.get('monster', [])
    
    if not monster_list:
        logger.warning(f"No monsters found in {file_path}")
        return monsters
    
    successful_count = 0
    failed_count = 0
    
    for monster_data in monster_list:
        monster_class = create_monster_class(monster_data)
        
        if monster_class:
            # Use lowercase name as key
            monster_key = monster_data['name'].lower()
            monsters[monster_key] = monster_class
            successful_count += 1
        else:
            failed_count += 1
    
    logger.info(
        f"Loaded {successful_count} monsters successfully, "
        f"{failed_count} failed to parse"
    )
    
    return monsters


def load_monsters_from_multiple_files(file_paths: List[str]) -> Dict[str, type[BaseMonster]]:
    """
    Load monsters from multiple JSON files.
    
    Args:
        file_paths: List of paths to JSON files
    
    Returns:
        Combined dictionary of all monster classes
    """
    all_monsters: Dict[str, type[BaseMonster]] = {}
    
    for file_path in file_paths:
        try:
            monsters = load_monsters_from_json(file_path)
            
            # Check for duplicates
            duplicates = set(all_monsters.keys()) & set(monsters.keys())
            if duplicates:
                logger.warning(
                    f"Found {len(duplicates)} duplicate monsters in {file_path}: "
                    f"{', '.join(sorted(duplicates)[:5])}..."
                )
            
            all_monsters.update(monsters)
            
        except FileNotFoundError:
            logger.error(f"Monster file not found: {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}", exc_info=True)
    
    return all_monsters


def get_monster_info(monster_class: type[BaseMonster]) -> Dict[str, Any]:
    """
    Extract information about a monster class.
    
    Args:
        monster_class: Monster class to inspect
    
    Returns:
        Dictionary with monster information
    """
    # Create a temporary instance to get stats
    temp_instance = monster_class()
    
    return {
        'name': temp_instance.name,
        'ac': temp_instance.ac,
        'max_hp': temp_instance.max_hp,
        'str': temp_instance.str,
        'dex': temp_instance.dex,
        'con': temp_instance.con,
        'int': temp_instance.int,
        'wis': temp_instance.wis,
        'cha': temp_instance.cha,
        'prof_bonus': temp_instance.prof_bonus,
        'resistances': getattr(temp_instance, 'resistances', []),
        'vulnerabilities': getattr(temp_instance, 'vulnerabilities', []),
        'immunities': getattr(temp_instance, 'immunities', [])
    }