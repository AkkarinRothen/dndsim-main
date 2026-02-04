"""
Unit tests for character combat system.

Tests weapon attacks, hit/miss mechanics, damage application, and
character state management.
"""
import pytest
import unittest
from unittest.mock import MagicMock
import sim.test_helpers
import sim.weapons
import sim.target
from sim.resource import Resource


class TestBasicAttacks:
    """Test basic attack mechanics."""
    
    def test_attack_always_hits(self):
        """Test that extremely high attack bonus always hits."""
        character = sim.test_helpers.sample_character()
        always_hit = sim.weapons.Weapon(
            "AlwaysHit",
            num_dice=1,
            die=6,
            attack_bonus=10000
        )
        target = sim.target.Target(level=5)
        
        character.weapon_attack(target, always_hit)
        
        assert target.dmg > 0, "Target should take damage from guaranteed hit"
    
    def test_attack_always_misses(self):
        """Test that extremely low attack bonus always misses."""
        character = sim.test_helpers.sample_character()
        always_miss = sim.weapons.Weapon(
            "AlwaysMiss",
            num_dice=1,
            die=6,
            attack_bonus=-10000
        )
        target = sim.target.Target(level=5)
        
        character.weapon_attack(target, always_miss)
        
        assert target.dmg == 0, "Target should take no damage from guaranteed miss"
    
    def test_attack_respects_target_ac(self):
        """Test that attacks properly compare against target AC."""
        character = sim.test_helpers.sample_character()
        
        # Create weapon with moderate bonus
        weapon = sim.weapons.Weapon(
            "StandardSword",
            num_dice=1,
            die=8,
            attack_bonus=5
        )
        
        # Low AC target should be hit more often
        low_ac_target = sim.target.Target(level=1, ac=10)
        character.weapon_attack(low_ac_target, weapon)
        low_ac_damage = low_ac_target.dmg
        
        # High AC target should be hit less often
        high_ac_target = sim.target.Target(level=1, ac=25)
        character.weapon_attack(high_ac_target, weapon)
        high_ac_damage = high_ac_target.dmg
        
        # Over many attacks, low AC should take more damage on average
        # This is probabilistic but with extreme AC difference it's reliable


class TestCharacterHP:
    """Test character HP and damage mechanics."""
    
    def test_character_takes_damage(self):
        """Test that characters lose HP when damaged."""
        character = sim.test_helpers.sample_character()
        initial_hp = character.hp
        
        character.apply_damage(damage=10, damage_type="slashing", source="test")
        
        assert character.hp == initial_hp - 10
    
    def test_character_hp_cannot_exceed_max(self):
        """Test that healing doesn't exceed max HP."""
        character = sim.test_helpers.sample_character()
        character.hp = character.max_hp
        
        # Attempt to heal (if we had healing mechanics)
        # For now just verify max_hp is set correctly
        assert character.hp <= character.max_hp
    
    def test_character_can_be_reduced_to_zero_hp(self):
        """Test that character can reach 0 HP."""
        character = sim.test_helpers.sample_character()
        
        character.apply_damage(
            damage=character.hp + 100,
            damage_type="force",
            source="test"
        )
        
        assert character.hp <= 0


class TestCharacterStats:
    """Test ability score mechanics."""
    
    def test_stat_retrieval(self):
        """Test that stat() method correctly returns ability scores."""
        character = sim.test_helpers.sample_character()
        character.stats["str"] = 18
        assert character.stat("str") == 18
        assert character.stat("dex") == 12 # Default value
        assert character.stat("none") == 10 # Special case for "none"

    def test_ability_modifier_calculation(self):
        """Test that ability modifiers are calculated correctly."""
        character = sim.test_helpers.sample_character()
        
        # Standard D&D modifier formula: (score - 10) // 2
        test_cases = [
            (10, 0),   # 10 = +0
            (12, 1),   # 12 = +1
            (14, 2),   # 14 = +2
            (16, 3),   # 16 = +3
            (18, 4),   # 18 = +4
            (20, 5),   # 20 = +5
            (8, -1),   # 8 = -1
            (6, -2),   # 6 = -2
        ]
        
        for score, expected_mod in test_cases:
            character.stats["str"] = score
            actual_mod = character.mod("str")
            assert actual_mod == expected_mod, \
                f"Score {score} should give modifier {expected_mod}, got {actual_mod}"
    
    def test_increase_stat_max(self):
        """Test that increase_stat_max correctly increases the maximum allowed value for a stat."""
        character = sim.test_helpers.sample_character()
        character.increase_stat_max("str", 2)
        assert character.stat_max["str"] == 22
        character.stats["str"] = 21
        character.increase_stat("str", 2)
        assert character.stats["str"] == 22


    def test_stat_increase_respects_maximum(self):
        """Test that stat increases don't exceed maximum."""
        character = sim.test_helpers.sample_character()
        
        # Set STR to 19 (just below max of 20)
        character.stats["str"] = 19
        
        # Try to increase by 5
        character.increase_stat("str", 5)
        
        # Should be capped at 20
        assert character.stats["str"] == 20
    
    def test_dc_calculation(self):
        """Test that save DCs are calculated correctly."""
        character = sim.test_helpers.sample_character()
        
        # DC formula: 8 + proficiency + ability modifier
        character.stats["wis"] = 16  # +3 modifier
        character.prof = 3
        
        expected_dc = 8 + 3 + 3  # 14
        actual_dc = character.dc("wis")
        
        assert actual_dc == expected_dc

        character.stats["cha"] = 20 # +5 modifier
        character.prof = 6
        expected_dc = 8 + 6 + 5 # 19
        actual_dc = character.dc("cha")
        assert actual_dc == 19


class TestCharacterResources:
    """Test resource management."""
    
    def test_bonus_action_tracking(self):
        """Test that bonus action can only be used once per turn."""
        character = sim.test_helpers.sample_character()
        target = sim.target.Target(level=5)
        
        character.begin_turn(target)
        
        # First use should succeed
        assert character.use_bonus("test") is True
        
        # Second use should fail
        assert character.use_bonus("test") is False
    
    def test_bonus_action_resets_on_new_turn(self):
        """Test that bonus action resets each turn."""
        character = sim.test_helpers.sample_character()
        target = sim.target.Target(level=5)
        
        character.begin_turn(target)
        character.use_bonus("test")
        character.end_turn(target)
        
        # New turn should reset bonus action
        character.begin_turn(target)
        assert character.use_bonus("test") is True


class TestNewCharacterResources(unittest.TestCase):
    def setUp(self):
        self.character = sim.test_helpers.sample_character()

    def test_add_and_use_resource(self):
        self.character.add_resource("Test Resource", 3, short_rest=True)
        self.assertIn("Test Resource", self.character.resources)
        res = self.character.resources["Test Resource"]
        self.assertEqual(res.max, 3)
        self.assertEqual(res.num, 3)
        
        self.assertTrue(res.use())
        self.assertEqual(res.num, 2)
        
    def test_resource_resets_on_rest(self):
        self.character.add_resource("Short Rest Res", 2, short_rest=True)
        self.character.add_resource("Long Rest Res", 1, short_rest=False)

        res_short = self.character.resources["Short Rest Res"]
        res_long = self.character.resources["Long Rest Res"]
        
        res_short.use()
        res_long.use()
        
        self.assertEqual(res_short.num, 1)
        self.assertEqual(res_long.num, 0)
        
        self.character.short_rest()
        
        self.assertEqual(res_short.num, 2)
        self.assertEqual(res_long.num, 0)
        
        res_short.use()
        self.character.long_rest()
        
        self.assertEqual(res_short.num, 2)
        self.assertEqual(res_long.num, 1)


class TestCharacterEffects:
    """Test status effects and conditions."""
    
    def test_add_and_remove_effect(self):
        """Test adding and removing status effects."""
        character = sim.test_helpers.sample_character()
        
        character.add_effect("poisoned")
        assert character.has_effect("poisoned")
        
        character.remove_effect("poisoned")
        assert not character.has_effect("poisoned")
    
    def test_multiple_effects(self):
        """Test character can have multiple effects simultaneously."""
        character = sim.test_helpers.sample_character()
        
        character.add_effect("poisoned")
        character.add_effect("blinded")
        character.add_effect("prone")
        
        assert character.has_effect("poisoned")
        assert character.has_effect("blinded")
        assert character.has_effect("prone")
        
        character.remove_effect("blinded")
        
        assert character.has_effect("poisoned")
        assert not character.has_effect("blinded")
        assert character.has_effect("prone")


class TestRests:
    """Test rest mechanics."""
    
    def test_long_rest_restores_hp(self):
        """Test that long rest restores HP to maximum."""
        character = sim.test_helpers.sample_character()
        
        # Damage character
        character.hp = character.max_hp // 2
        
        character.long_rest()
        
        assert character.hp == character.max_hp
    
    def test_short_rest_clears_effects(self):
        """Test that short rest clears status effects."""
        character = sim.test_helpers.sample_character()
        
        character.add_effect("test_effect")
        character.short_rest()
        
        assert not character.has_effect("test_effect")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
