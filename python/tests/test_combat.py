import unittest
import sys
import os

# Add the parent directory to the sys.path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sim.party_sim import Combat
from classes.fighter import Fighter
from classes.cleric import Cleric
from monsters.goblin import Goblin
from monsters.orc import Orc
from monsters.evil_mage import EvilMage
from monsters.acolyte_healer import AcolyteHealer

class TestCombat(unittest.TestCase):
    def test_full_combat_simulation(self):
        """
        Tests a full combat from start to finish between a Fighter and a Goblin.
        """
        # 1. Setup
        party = [Fighter(level=1)]
        enemies = [Goblin()]
        
        combat = Combat(party=party, enemies=enemies)
        
        # 2. Execute
        result = combat.run_combat()
        
        # 3. Assert
        self.assertIsNotNone(result, "El resultado del combate no debería ser nulo.")
        
        winner = result.get('winner')
        self.assertIn(winner, ['party', 'monsters'], "El ganador debe ser 'party' o 'monsters'.")
        
        rounds = result.get('rounds')
        self.assertIsInstance(rounds, int, "Las rondas deben ser un número entero.")
        self.assertGreaterEqual(rounds, 0, "El combate debería durar al menos cero rondas.")
        self.assertLess(rounds, 20, "El combate no debería exceder un número de rondas razonable.")

    def test_brute_ai_target_selection(self):
        """
        Tests that a 'brute' AI monster correctly targets the highest threat character.
        This test is made deterministic by manually setting initiative.
        """
        # 1. Setup
        party = [Fighter(level=5, name="Fighter"), Cleric(level=5, name="Cleric")]
        enemies = [Orc()]
        combat = Combat(party=party, enemies=enemies)

        # 2. Execute
        combat.setup_combat()
        # Manually set initiative to ensure the Orc acts first
        for combatant in combat.turn_order:
            if combatant.name == "Orc":
                combatant.initiative = 99
            else:
                combatant.initiative = 1
        combat.turn_order = sorted(combat.turn_order, key=lambda c: c.initiative, reverse=True)
        
        # Run combat until it's over
        while not combat.is_over():
            combat.run_combat_turn()

        # 3. Assert
        orc_turn_log = next((log for log in combat.combat_log if "Orc (AI: Brute)" in log), None)
        
        self.assertIsNotNone(orc_turn_log, "No se encontró ninguna entrada de log para el turno del Orco.")
        self.assertIn("targets Fighter", orc_turn_log, "El Orco (Brute AI) debería haber atacado al Fighter.")

    def test_caster_ai_uses_spell(self):
        """
        Tests that a 'caster' AI monster prioritizes using a spell.
        This test is made deterministic by manually setting initiative.
        """
        # 1. Setup
        party = [Fighter(level=3, name="Fighter")]
        enemies = [EvilMage()]
        combat = Combat(party=party, enemies=enemies)
        
        # 2. Execute
        combat.setup_combat()
        # Manually set initiative to ensure the Mage acts first
        for combatant in combat.turn_order:
            if combatant.name == "Evil Mage":
                combatant.initiative = 99
            else:
                combatant.initiative = 1
        combat.turn_order = sorted(combat.turn_order, key=lambda c: c.initiative, reverse=True)
        
        # Run combat until it's over
        while not combat.is_over():
            combat.run_combat_turn()

        # 3. Assert
        mage_cast_log = next((log for log in combat.combat_log if "Evil Mage casts Magic Missile" in log), None)
        
        self.assertIsNotNone(mage_cast_log, "No se encontró ninguna entrada de log para el Evil Mage casteando Magic Missile.")

    def test_support_ai_heals_ally(self):
        """
        Tests that a 'support' AI monster heals an injured ally.
        This test is made deterministic by manually setting initiative.
        """
        # 1. Setup
        party = [Fighter(level=1, name="Fighter")]
        # Give the healers different names to distinguish them in logs
        healer1 = AcolyteHealer()
        healer1.name = "Healer 1"
        healer2 = AcolyteHealer()
        healer2.name = "Healer 2"
        enemies = [healer1, healer2]
        
        combat = Combat(party=party, enemies=enemies)
        combat.setup_combat()

        # Manually damage one of the healers
        injured_healer = combat.get_combatant(healer1)
        injured_healer.entity.hp -= 5
        injured_healer.current_hp -= 5

        # Manually set initiative to ensure the other healer acts first
        for combatant in combat.turn_order:
            if combatant.name == "Healer 2": # The healthy one
                combatant.initiative = 99
            else:
                combatant.initiative = 1
        combat.turn_order = sorted(combat.turn_order, key=lambda c: c.initiative, reverse=True)

        # 2. Execute
        # Run just the first turn
        combat.run_combat_turn()

        # 3. Assert
        heal_log = next((log for log in combat.combat_log if "Healer 2 casts Cure Wounds on Healer 1" in log), None)
        
        self.assertIsNotNone(heal_log, "El Sanador 2 debería haber curado al Sanador 1.")


if __name__ == '__main__':
    unittest.main()
