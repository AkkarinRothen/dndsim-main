import unittest
import sys
import os

# Add the parent directory to the sys.path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from combat_manager import CombatManager, CombatConfig
import configs
import monster_configs
import sim.party_sim
from monsters.goblin import Goblin
from simulator_exceptions import CharacterLoadException


class TestCombatManager(unittest.TestCase):
    def setUp(self):
        """Set up a common manager for tests."""
        self.configs_module = configs
        self.monster_configs_module = monster_configs
        self.party_sim_module = sim.party_sim

    def test_create_party_instances(self):
        """Verifica la creación correcta de instancias de party."""
        config = CombatConfig(
            party_members=["fighter", "wizard"],
            enemies=[(Goblin, 2)],
            level=5
        )
        
        manager = CombatManager(
            config=config,
            configs_module=self.configs_module,
            monster_configs_module=self.monster_configs_module,
            party_sim_module=self.party_sim_module
        )
        
        party = manager.create_party_instances()
        
        self.assertEqual(len(party), 2, "El número de miembros del party no es el esperado")
        self.assertEqual(party[0].level, 5, "El nivel del primer miembro del party no es correcto")
        self.assertEqual(party[1].level, 5, "El nivel del segundo miembro del party no es correcto")
        self.assertEqual(party[0].name, "Fighter", "El nombre del primer miembro no es correcto")
        self.assertEqual(party[1].name, "Evocation Wizard", "El nombre del segundo miembro no es correcto")

    def test_create_party_with_invalid_character(self):
        """Verifica que se lanza una excepción con un personaje inválido."""
        config = CombatConfig(
            party_members=["fighter", "non_existent_character"],
            enemies=[(Goblin, 1)],
            level=1
        )
        
        manager = CombatManager(
            config=config,
            configs_module=self.configs_module,
            monster_configs_module=self.monster_configs_module,
            party_sim_module=self.party_sim_module
        )
        
        with self.assertRaises(CharacterLoadException):
            manager.create_party_instances()


if __name__ == '__main__':
    unittest.main()
