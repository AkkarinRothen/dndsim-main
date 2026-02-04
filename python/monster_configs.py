import os
import json
from sim.monster import BaseMonster
from monsters.goblin import Goblin
from monsters.orc import Orc
from monster_parser import load_monsters_from_json

# Dictionary to hold the actual monster class objects once loaded
_MONSTER_CACHE = {}

# Dictionary to hold monster names mapped to their JSON file paths and the specific monster name within that file
# This is built at import time, but parsing of the monster data is deferred.
_MONSTER_PATHS = {
    "goblin": (None, Goblin), # Manually defined monsters don't have a file path
    "orc": (None, Orc),
}

# Dynamically find monster JSON files and store their paths
BESTIARY_DATA_PATH = os.path.join(os.path.dirname(__file__), 'creatures', '5etools-src', 'data', 'bestiary')

if os.path.exists(BESTIARY_DATA_PATH):
    for filename in os.listdir(BESTIARY_DATA_PATH):
        if filename.startswith('bestiary-') and filename.endswith('.json'):
            file_path = os.path.join(BESTIARY_DATA_PATH, filename)
            try:
                # Read the file to get monster names without full parsing
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for monster_data in data.get('monster', []):
                        name = monster_data.get('name')
                        if name:
                            _MONSTER_PATHS[name.lower()] = (file_path, name)
            except Exception as e:
                print(f"Error indexing monsters from {filename}: {e}")

def _load_monster_from_file(file_path: str, monster_name_in_file: str) -> type[BaseMonster] | None:
    """
    Loads a specific monster class from a given JSON file.
    """
    try:
        # load_monsters_from_json returns a dict {name.lower(): MonsterClass}
        loaded_monsters = load_monsters_from_json(file_path)
        return loaded_monsters.get(monster_name_in_file.lower())
    except Exception as e:
        print(f"Error loading specific monster '{monster_name_in_file}' from {file_path}: {e}")
        return None

def get_monster_class(name: str) -> type[BaseMonster] | None:
    """
    Retrieves a monster class by its name, loading it if not already in cache.
    """
    name_lower = name.lower()
    if name_lower in _MONSTER_CACHE:
        return _MONSTER_CACHE[name_lower]

    if name_lower in _MONSTER_PATHS:
        file_path_info = _MONSTER_PATHS[name_lower]
        file_path = file_path_info[0]
        original_name = file_path_info[1]

        if file_path is None: # Handle manually defined monsters
            monster_class = original_name # original_name is the class itself for manual monsters
            _MONSTER_CACHE[name_lower] = monster_class
            return monster_class
        else:
            monster_class = _load_monster_from_file(file_path, original_name)
            if monster_class:
                _MONSTER_CACHE[name_lower] = monster_class
                return monster_class
    return None

def get_all_monster_names() -> list[str]:
    """
    Returns a sorted list of all available monster names (indexed, not fully loaded).
    """
    return sorted(list(_MONSTER_PATHS.keys()))

