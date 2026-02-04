"""
Flask web application for D&D 5e Combat Simulator.

This module provides a web interface for running interactive combat simulations,
allowing users to configure parties, enemies, and run turn-based combat.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict

from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import BadRequest
from simulator_exceptions import MonsterLoadException, SimulatorException

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import configs
import monster_configs
import sim.party_sim
from combat_manager import CombatConfig, CombatManager
from combat_presets import COMBAT_PRESETS
from simulator_exceptions import MonsterLoadException, SimulatorException


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


class SessionKeys:
    """Constants for session key names."""
    COMBAT_DATA = 'combat_data'


class CombatStateManager:
    """Manages combat state serialization and deserialization for sessions."""
    
    @staticmethod
    def serialize_combat(combat: sim.party_sim.Combat, combat_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize combat state to a JSON-compatible dictionary.
        
        Args:
            combat: The combat instance to serialize
            combat_config: The combat configuration to include
            
        Returns:
            Dictionary containing serializable combat state
        """
        return {
            'config': combat_config,
            'combatants': [
                {
                    'name': c.name,
                    'hp': c.current_hp,
                    'max_hp': c.entity.max_hp,
                    'is_down': c.is_down
                }
                for c in combat.combatants
            ],
            'turn_order': [c.name for c in combat.turn_order],
            'rounds': combat.rounds,
            'log': combat.combat_log
        }
    
    @staticmethod
    def deserialize_combat(
        session_data: Dict[str, Any],
        configs_module: Any,
        monster_configs_module: Any,
        party_sim_module: Any
    ) -> sim.party_sim.Combat:
        """
        Reconstruct a Combat object from session data.
        
        Args:
            session_data: Serialized combat state
            configs_module: Character configs module
            monster_configs_module: Monster configs module
            party_sim_module: Party sim module
            
        Returns:
            Reconstructed Combat instance
            
        Raises:
            MonsterLoadException: If a monster class cannot be found
        """
        # Reconstruct enemy classes from names
        enemy_classes_and_counts: List[Tuple[type, int]] = []
        for enemy_name, count in session_data['config']['enemies']:
            enemy_class = monster_configs_module.get_monster_class(enemy_name)
            if not enemy_class:
                raise MonsterLoadException(
                    f"Monster '{enemy_name}' not found during session restore."
                )
            enemy_classes_and_counts.append((enemy_class, count))

        # Create combat config
        config = CombatConfig(
            party_members=session_data['config']['party'],
            enemies=enemy_classes_and_counts,
            level=session_data['config']['level']
        )

        # Create combat manager and combat object
        combat_manager = CombatManager(
            config, configs_module, monster_configs_module, party_sim_module
        )
        combat = combat_manager.create_combat(use_hooks=False)

        # Restore combatant state
        combatant_map = {c.name: c for c in combat.combatants}
        for combatant_data in session_data['combatants']:
            if combatant_data['name'] in combatant_map:
                c = combatant_map[combatant_data['name']]
                c.entity.hp = combatant_data['hp']
                c.current_hp = combatant_data['hp']
                c.is_down = combatant_data['is_down']
        
        # Ensure spell slots are initialized for party members after deserialization
        for party_member_combatant in combat.party:
            if hasattr(party_member_combatant.entity, 'spells') and party_member_combatant.entity.spells:
                party_member_combatant.entity.long_rest()
                app.logger.debug(f"Performed long_rest for {party_member_combatant.name} to initialize spell slots.")

        # Restore turn order
        restored_turn_order = [
            combatant_map[name] 
            for name in session_data['turn_order'] 
            if name in combatant_map
        ]
        combat.turn_order = restored_turn_order
        combat.rounds = session_data['rounds']
        combat.combat_log = session_data['log']

        # If turn order restoration failed but combatants exist, re-establish turn order
        if not combat.turn_order and combat.combatants:
            app.logger.warning("Restored turn order is empty, but combatants exist. Re-establishing turn order without resetting HP.")
            combat.recreate_turn_order()

        return combat


def get_combat_state_json(combat: sim.party_sim.Combat) -> Dict[str, Any]:
    """
    Create a JSON-serializable representation of current combat state.
    
    Args:
        combat: The combat instance
        
    Returns:
        Dictionary with combat state information
    """
    is_over = combat.is_over()
    
    return {
        'rounds': combat.rounds,
        'combatants': [
            {
                'name': c.name,
                'team': c.team,
                'hp': c.current_hp,
                'max_hp': c.entity.max_hp,
                'is_down': c.is_down,
            }
            for c in combat.combatants
        ],
        'turn_order': [c.name for c in combat.turn_order],
        'log': combat.combat_log,
        'is_over': is_over,
        'winner': combat._determine_winner() if is_over else None
    }


# Helper for standardized JSON error responses
def json_error_response(message: str, status_code: int) -> Tuple[Dict[str, Any], int]:
    """
    Creates a standardized JSON error response.
    
    Args:
        message: The error message.
        status_code: The HTTP status code for the error.
        
    Returns:
        A tuple containing the JSON response dictionary and the status code.
    """
    return jsonify({'error': message}), status_code

# Centralized error handlers
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    """Handle BadRequest exceptions globally."""
    app.logger.warning(f"Bad request: {e}")
    return json_error_response(str(e), 400)

@app.errorhandler(MonsterLoadException)
def handle_monster_load_exception(e):
    """Handle MonsterLoadException globally as a Bad Request."""
    app.logger.error(f"Simulator error: {e}", exc_info=True)
    return json_error_response(str(e), 400)

@app.errorhandler(SimulatorException)
def handle_simulator_exception(e):
    """Handle SimulatorException globally as a Bad Request."""
    app.logger.error(f"Simulator error: {e}", exc_info=True)
    return json_error_response(str(e), 400)

@app.errorhandler(Exception)
def handle_general_exception(e):
    """Handle all other exceptions globally."""
    app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    return json_error_response('An unexpected error occurred', 500)

@app.route('/')
def index() -> str:
    """
    Render the main application page.
    
    Returns:
        Rendered HTML template
    """
    characters = list(configs.CONFIGS.keys())
    monsters = monster_configs.get_all_monster_names()
    
    return render_template(
        'index.html',
        characters=characters,
        monsters=monsters,
        presets=COMBAT_PRESETS
    )


@app.route('/api/start_combat', methods=['POST'])
def start_combat():
    """
    Start a new combat simulation.
    
    Expected JSON payload:
        - party: List[str] - Character keys
        - enemies: List[Dict] - Enemy configurations with 'name' and 'count'
        - level: int - Party level
        
    Returns:
        JSON response with initial combat state or error
    """
    data = request.get_json(silent=True)
    
    if data is None:
        raise BadRequest("Request must contain valid JSON data.")
    
    # Validate required fields
    required_fields = ['party', 'enemies', 'level']
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Parse enemies
    enemy_classes_and_counts: List[Tuple[type, int]] = []
    for enemy_data in data['enemies']:
        if 'name' not in enemy_data or 'count' not in enemy_data:
            raise BadRequest("Each enemy must have 'name' and 'count' fields")
            
        enemy_class = monster_configs.get_monster_class(enemy_data['name'])
        if not enemy_class:
            raise MonsterLoadException(f"Monster '{enemy_data['name']}' not found.")
            
        enemy_classes_and_counts.append((enemy_class, int(enemy_data['count'])))

    # Store config for session (with names, not classes)
    combat_config_for_session = {
        "party": data['party'],
        "enemies": [(name, count) for (_, count), enemy_data 
                   in zip(enemy_classes_and_counts, data['enemies'])
                   for name in [enemy_data['name']]],
        "level": int(data['level'])
    }
    
    # Create combat
    config = CombatConfig(
        party_members=combat_config_for_session['party'],
        enemies=enemy_classes_and_counts,
        level=combat_config_for_session['level']
    )
    
    combat_manager = CombatManager(config, configs, monster_configs, sim.party_sim)
    combat = combat_manager.create_combat(use_hooks=False)
    combat.setup_combat()

    # Store in session
    session[SessionKeys.COMBAT_DATA] = CombatStateManager.serialize_combat(combat, combat_config_for_session)
    
    app.logger.info(f"Started combat: {len(data['party'])} party members vs "
                   f"{len(data['enemies'])} enemy types")
    
    return jsonify(get_combat_state_json(combat))


@app.route('/api/next_turn', methods=['POST'])
def next_turn():
    """
    Execute the next turn of combat.
    
    Returns:
        JSON response with updated combat state or error
    """
    if SessionKeys.COMBAT_DATA not in session:
        return jsonify({
            'error': 'No active combat. Please start a new combat.'
        }), 400

    session_data = session[SessionKeys.COMBAT_DATA]
    
    # Reconstruct combat from session
    combat = CombatStateManager.deserialize_combat(
        session_data, configs, monster_configs, sim.party_sim
    )
    
    # Execute turn if combat is ongoing
    if not combat.is_over():
        actor = combat.turn_order[0]
        app.logger.info(f"Executing turn for {actor.name} (Round {combat.rounds})")
        combat.run_combat_turn()
        app.logger.debug(f"Executed turn, now at round {combat.rounds}")

    # Update session with new state
    session[SessionKeys.COMBAT_DATA] = CombatStateManager.serialize_combat(combat, session_data['config'])
    
    if combat.is_over():
        app.logger.info(f"Combat ended. Winner: {combat._determine_winner()}")

    return jsonify(get_combat_state_json(combat))


@app.route('/api/reset_combat', methods=['POST'])
def reset_combat():
    """
    Reset the current combat session.
    
    Returns:
        JSON response confirming reset
    """
    if SessionKeys.COMBAT_DATA in session:
        session.pop(SessionKeys.COMBAT_DATA)
        app.logger.info("Combat session reset")
    
    return jsonify({'success': True, 'message': 'Combat reset successfully'})


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    app.logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(
        debug=False,
        use_reloader=False,
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000))
    )