"""
Test Suite for Flask Combat Simulator Application.

This module provides comprehensive tests for the web application endpoints,
session management, and combat state handling.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app, SessionKeys


@pytest.fixture
def app():
    """
    Create and configure a new app instance for each test.
    
    Yields:
        Flask application configured for testing
    """
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-for-sessions"
    })
    yield flask_app


@pytest.fixture
def client(app):
    """
    Create a test client for the app.
    
    Args:
        app: Flask application fixture
    
    Yields:
        Flask test client
    """
    return app.test_client()


@pytest.fixture
def sample_combat_config() -> Dict[str, Any]:
    """
    Provide a sample combat configuration for tests.
    
    Returns:
        Valid combat configuration dictionary
    """
    return {
        "level": 1,
        "party": ["fighter"],
        "enemies": [{"name": "goblin", "count": 1}]
    }


class TestIndexRoute:
    """Tests for the index page endpoint."""
    
    def test_index_loads(self, client):
        """Test that the index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Combat Simulator' in response.data
    
    def test_index_contains_form(self, client):
        """Test that the index page contains the combat setup form."""
        response = client.get('/')
        assert b'combat-setup-form' in response.data
        assert b'party-select' in response.data
        assert b'level-select' in response.data


class TestStartCombatAPI:
    """Tests for the /api/start_combat endpoint."""
    
    def test_start_combat_success(self, client, sample_combat_config):
        """Test successful combat initialization."""
        response = client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'rounds' in data
        assert 'combatants' in data
        assert 'turn_order' in data
        assert 'log' in data
        assert 'is_over' in data
        
        # Verify combatants
        assert len(data['combatants']) == 2  # 1 fighter + 1 goblin
        
        combatant_names = [c['name'] for c in data['combatants']]
        assert 'Fighter' in combatant_names or any('Fighter' in name for name in combatant_names)
        assert 'Goblin' in combatant_names or any('Goblin' in name for name in combatant_names)
    
    def test_start_combat_multiple_enemies(self, client):
        """Test combat with multiple enemy types."""
        config = {
            "level": 2,
            "party": ["fighter", "wizard"],
            "enemies": [
                {"name": "goblin", "count": 2},
                {"name": "orc", "count": 1}
            ]
        }
        
        response = client.post(
            '/api/start_combat',
            data=json.dumps(config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should have 2 party members + 3 enemies
        assert len(data['combatants']) == 5
    
    def test_start_combat_missing_fields(self, client):
        """Test that missing required fields are rejected."""
        incomplete_config = {
            "level": 1,
            "party": ["fighter"]
            # Missing 'enemies' field
        }
        
        response = client.post(
            '/api/start_combat',
            data=json.dumps(incomplete_config),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_start_combat_invalid_monster(self, client):
        """Test that invalid monster names are rejected."""
        config = {
            "level": 1,
            "party": ["fighter"],
            "enemies": [{"name": "nonexistent_monster", "count": 1}]
        }
        
        response = client.post(
            '/api/start_combat',
            data=json.dumps(config),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_start_combat_no_json(self, client):
        """Test that requests without JSON are rejected."""
        response = client.post('/api/start_combat')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_start_combat_invalid_level(self, client):
        """Test that invalid level values are handled."""
        config = {
            "level": 0,  # Invalid level
            "party": ["fighter"],
            "enemies": [{"name": "goblin", "count": 1}]
        }
        
        response = client.post(
            '/api/start_combat',
            data=json.dumps(config),
            content_type='application/json'
        )
        
        # Should either reject or handle gracefully
        assert response.status_code in [400, 500]


class TestNextTurnAPI:
    """Tests for the /api/next_turn endpoint."""
    
    def test_next_turn_success(self, client, sample_combat_config):
        """Test executing a combat turn."""
        # First, start a combat
        start_response = client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        assert start_response.status_code == 200
        
        initial_data = start_response.get_json()
        initial_log_length = len(initial_data['log'])
        
        # Execute a turn
        turn_response = client.post('/api/next_turn')
        
        assert turn_response.status_code == 200
        turn_data = turn_response.get_json()
        
        # Verify response structure
        assert 'rounds' in turn_data
        assert 'combatants' in turn_data
        assert 'log' in turn_data
        
        # Combat log should have new entries
        assert len(turn_data['log']) >= initial_log_length
    
    def test_next_turn_without_combat(self, client):
        """Test that next_turn fails without an active combat."""
        response = client.post('/api/next_turn')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'no active combat' in data['error'].lower() or 'no combat' in data['error'].lower()
    
    def test_multiple_turns(self, client, sample_combat_config):
        """Test executing multiple combat turns."""
        # Start combat
        client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        
        # Execute multiple turns
        for _ in range(5):
            response = client.post('/api/next_turn')
            assert response.status_code == 200
            
            data = response.get_json()
            
            # If combat ends, stop testing
            if data.get('is_over'):
                assert data.get('winner') in ['party', 'enemies']
                break
    
    def test_turn_after_combat_end(self, client, sample_combat_config):
        """Test that turns can be called after combat ends without errors."""
        # Start combat
        client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        
        # Execute turns until combat ends (max 100 to prevent infinite loop)
        for _ in range(100):
            response = client.post('/api/next_turn')
            assert response.status_code == 200
            
            data = response.get_json()
            if data.get('is_over'):
                # Try one more turn after combat is over
                final_response = client.post('/api/next_turn')
                assert final_response.status_code == 200
                break


class TestResetCombatAPI:
    """Tests for the /api/reset_combat endpoint."""
    
    def test_reset_combat(self, client, sample_combat_config):
        """Test resetting an active combat."""
        # Start a combat
        client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        
        # Reset combat
        response = client.post('/api/reset_combat')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('success') is True
    
    def test_reset_without_combat(self, client):
        """Test that reset works even without an active combat."""
        response = client.post('/api/reset_combat')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('success') is True


class TestSessionManagement:
    """Tests for session state management."""
    
    def test_session_persists_between_turns(self, client, sample_combat_config):
        """Test that combat state persists in session across requests."""
        # Start combat
        start_response = client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        start_data = start_response.get_json()
        
        # Execute a turn
        turn_response = client.post('/api/next_turn')
        turn_data = turn_response.get_json()
        
        # Round should have progressed
        assert turn_data['rounds'] >= start_data['rounds']
    
    def test_new_combat_replaces_session(self, client, sample_combat_config):
        """Test that starting a new combat replaces the session data."""
        # Start first combat
        client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        
        # Execute some turns
        for _ in range(3):
            client.post('/api/next_turn')
        
        # Start a new combat
        new_config = {
            "level": 2,
            "party": ["wizard"],
            "enemies": [{"name": "orc", "count": 1}]
        }
        
        response = client.post(
            '/api/start_combat',
            data=json.dumps(new_config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be a fresh combat
        assert data['rounds'] == 0 or data['rounds'] == 1


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_404_on_invalid_endpoint(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get('/api/invalid_endpoint')
        assert response.status_code == 404
    
    def test_malformed_json(self, client):
        """Test that malformed JSON is handled gracefully."""
        response = client.post(
            '/api/start_combat',
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestCombatStateValidation:
    """Tests for combat state validation and integrity."""
    
    def test_combatants_have_valid_hp(self, client, sample_combat_config):
        """Test that all combatants have valid HP values."""
        response = client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        
        data = response.get_json()
        
        for combatant in data['combatants']:
            assert 'hp' in combatant
            assert 'max_hp' in combatant
            assert combatant['hp'] >= 0
            assert combatant['max_hp'] > 0
            assert combatant['hp'] <= combatant['max_hp']
    
    def test_teams_are_valid(self, client, sample_combat_config):
        """Test that all combatants have valid team assignments."""
        response = client.post(
            '/api/start_combat',
            data=json.dumps(sample_combat_config),
            content_type='application/json'
        )
        
        data = response.get_json()
        
        for combatant in data['combatants']:
            assert 'team' in combatant
            assert combatant['team'] in ['party', 'enemies']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])