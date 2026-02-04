"""
D&D 5e Interactive Combat Simulator - Versión Mejorada

Este simulador permite:
- Simulaciones individuales de DPR
- Combates interactivos de party
- Creación de personajes personalizados
"""
import os
import json
import pickle
import logging
from typing import Optional, List
from datetime import datetime
from prettytable import PrettyTable

# Imports del proyecto
import sim
import sim.party_sim
import configs
import monster_configs
from sim.character_config import CharacterConfig

# Imports de módulos mejorados
from colors import Colors
from constants import CombatConstants, CUSTOM_CHARS_DIR
from ui_utils import (
    clear_screen, print_separator, print_section_header, print_banner,
    prompt_yes_no, get_positive_int_input, select_from_menu, display_hp_bar
)
from combat_display import CombatDisplay
from combat_manager import CombatManager, CombatConfig, CombatCommands
from validation import (
    validate_level, validate_combat_config, find_combatant_by_partial_name
)
from simulator_exceptions import (
    SimulatorException, CharacterLoadException, MonsterLoadException,
    ValidationException, CombatSetupException
)
from combat_presets import COMBAT_PRESETS

# Configurar logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('interactive_sim')


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def _load_all_characters():
    """
    Carga todos los personajes desde configs y el directorio custom_chars.
    
    Returns:
        dict: Diccionario con todas las configuraciones de personajes
    """
    all_chars = {}
    
    # Cargar personajes built-in
    for key, config in configs.CONFIGS.items():
        all_chars[key] = {
            "name": config.name,
            "class": config.constructor.__name__,
            "args": config.args,
            "source": "Built-in"
        }
    
    # Cargar personajes personalizados
    if os.path.exists(CUSTOM_CHARS_DIR):
        for filename in os.listdir(CUSTOM_CHARS_DIR):
            if filename.endswith(".json"):
                char_key = filename.replace(".json", "")
                try:
                    with open(os.path.join(CUSTOM_CHARS_DIR, filename), 'r', encoding='utf-8') as f:
                        char_data = json.load(f)
                        char_data["source"] = "Custom"
                        all_chars[char_key] = char_data
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"No se pudo cargar '{filename}': {e}")
                    print(f"{Colors.WARNING}⚠️  Advertencia: No se pudo cargar '{filename}': {e}{Colors.ENDC}")
    
    return all_chars


def _display_combatant_info(combatant_wrapper):
    """
    Muestra información detallada de un combatiente.
    
    Args:
        combatant_wrapper: Wrapper de Combatant
    """
    CombatDisplay.show_combatant_details(combatant_wrapper)


def _save_combat_state(combat, filename):
    """
    Guarda el estado del combate a un archivo.
    
    Args:
        combat: Instancia de Combat
        filename: Nombre del archivo (sin extensión)
    """
    if not filename.endswith('.pkl'):
        filename = f"{filename}.pkl"
    
    try:
        with open(filename, 'wb') as f:
            pickle.dump(combat, f)
        print(f"{Colors.OKGREEN}✓ Combate guardado en '{filename}'{Colors.ENDC}")
        logger.info(f"Combate guardado en {filename}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error al guardar: {e}{Colors.ENDC}")
        logger.error(f"Error al guardar combate: {e}", exc_info=True)


def _load_combat_state(filename):
    """
    Carga el estado del combate desde un archivo.
    
    Args:
        filename: Nombre del archivo (sin extensión)
    
    Returns:
        Combat o None: Combate cargado o None si hubo error
    """
    if not filename.endswith('.pkl'):
        filename = f"{filename}.pkl"
    
    if not os.path.exists(filename):
        print(f"{Colors.FAIL}❌ Archivo '{filename}' no encontrado{Colors.ENDC}")
        return None
    
    try:
        with open(filename, 'rb') as f:
            combat = pickle.load(f)
        print(f"{Colors.OKGREEN}✓ Combate cargado desde '{filename}'{Colors.ENDC}")
        logger.info(f"Combate cargado desde {filename}")
        return combat
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error al cargar: {e}{Colors.ENDC}")
        logger.error(f"Error al cargar combate: {e}", exc_info=True)
        return None


# ============================================================================
# MENÚ PRINCIPAL
# ============================================================================

def display_main_menu():
    """
    Muestra el menú principal y devuelve la elección del usuario.
    
    Returns:
        str: Opción elegida por el usuario
    """
    clear_screen()
    print_banner()
    
    print(f"{Colors.BOLD}{Colors.OKCYAN}📋 MENÚ PRINCIPAL{Colors.ENDC}\n")
    
    options = [
        ("1", "⚔️  Simulación Individual de DPR", "Calcula el daño por round de personajes"),
        ("2", "🗡️  Simulación de Combate de Party", "Simula batallas completas de grupo"),
        ("3", "📜 Cargar Combate Prediseñado", "Elige un escenario de combate listo para usar"),
        ("4", "✨ Crear Nuevo Personaje", "Diseña un héroe personalizado"),
        ("5", "🚪 Salir", "Abandona el simulador")
    ]
    
    for num, title, desc in options:
        print(f"{Colors.BOLD}{Colors.WARNING}{num}.{Colors.ENDC} {Colors.BOLD}{Colors.WHITE}{title}{Colors.ENDC}")
        print(f"   {Colors.GRAY}{desc}{Colors.ENDC}\n")
    
    print_separator("─")
    choice = input(f"{Colors.BOLD}{Colors.OKCYAN}👉 Elige una opción: {Colors.ENDC}")
    return choice



# ============================================================================
# CREACIÓN DE PERSONAJES
# ============================================================================

def create_character():
    """Guía al usuario para crear un nuevo personaje."""
    clear_screen()
    print_section_header("CREADOR DE PERSONAJES", "✨")
    
    all_characters = _load_all_characters()
    templates = list(all_characters.keys())
    
    print(f"{Colors.BOLD}{Colors.OKCYAN}¿Quieres empezar desde cero o usar una plantilla?{Colors.ENDC}\n")
    print(f"{Colors.BOLD}{Colors.WARNING}0.{Colors.ENDC} {Colors.WHITE}🆕 Empezar desde cero{Colors.ENDC}")
    
    for i, t_name in enumerate(templates, 1):
        source = all_characters[t_name]['source']
        icon = "🏰" if source == "Built-in" else "⭐"
        color = Colors.OKBLUE if source == "Built-in" else Colors.OKGREEN
        print(f"{Colors.BOLD}{Colors.WARNING}{i}.{Colors.ENDC} {color}{icon} {t_name} ({source}){Colors.ENDC}")
    
    print_separator("─")
    choice = input(f"{Colors.BOLD}{Colors.OKCYAN}👉 Elige una plantilla (0-{len(templates)}): {Colors.ENDC}")
    
    char_data = {"name": "", "class": "", "args": {}}
    
    try:
        choice_idx = int(choice)
        if choice_idx > 0 and choice_idx <= len(templates):
            template_key = templates[choice_idx - 1]
            char_data = all_characters[template_key].copy()
            print(f"{Colors.OKGREEN}✓ Usando '{template_key}' como plantilla.{Colors.ENDC}")
        elif choice_idx == 0:
            print(f"{Colors.OKGREEN}✓ Empezando desde cero.{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠️  Opción inválida. Empezando desde cero.{Colors.ENDC}")
    except ValueError:
        print(f"{Colors.WARNING}⚠️  Entrada inválida. Empezando desde cero.{Colors.ENDC}")
    
    new_name = input(f"\n{Colors.OKCYAN}📝 Nombre del personaje{Colors.ENDC} (o Enter para '{char_data.get('name', '')}'): ")
    if new_name:
        char_data['name'] = new_name
    
    if not char_data.get('class'):
        available_classes = list(configs.CLASS_REGISTRY.keys())
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}🎭 Clases Disponibles:{Colors.ENDC}")
        
        class_icons = {
            "Fighter": "⚔️", "Wizard": "🧙", "Rogue": "🗡️", "Cleric": "✨",
            "Barbarian": "🪓", "Ranger": "🏹", "Paladin": "🛡️", "Warlock": "🔮",
            "Sorcerer": "⚡", "Bard": "🎵", "Druid": "🌿", "Monk": "👊"
        }
        
        for i, class_name in enumerate(available_classes, 1):
            icon = class_icons.get(class_name, "🎲")
            print(f"{Colors.WARNING}{i}.{Colors.ENDC} {icon} {Colors.WHITE}{class_name}{Colors.ENDC}")
        
        print_separator("─")
        try:
            class_choice = int(input(f"{Colors.OKCYAN}👉 Elige una clase (1-{len(available_classes)}): {Colors.ENDC}"))
            if 1 <= class_choice <= len(available_classes):
                char_data['class'] = available_classes[class_choice - 1]
                print(f"{Colors.OKGREEN}✓ Clase seleccionada: {char_data['class']}{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Opción inválida. Abortando.{Colors.ENDC}")
                input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
                return
        except ValueError:
            print(f"{Colors.FAIL}❌ Entrada inválida. Abortando.{Colors.ENDC}")
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
            return
    
    # Remover 'source' antes de guardar
    char_data.pop('source', None)
    
    # Sanitizar nombre para archivo
    file_name_base = "".join(x for x in char_data['name'] if x.isalnum() or x in " _-").rstrip().lower().replace(" ", "_")
    if not file_name_base:
        print(f"{Colors.FAIL}❌ El nombre del personaje es inválido. Abortando.{Colors.ENDC}")
        input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
        return
    
    file_path = os.path.join(CUSTOM_CHARS_DIR, f"{file_name_base}.json")
    
    if os.path.exists(file_path):
        if not prompt_yes_no(f"'{file_path}' ya existe. ¿Sobrescribir?", default=False):
            print(f"{Colors.FAIL}❌ Creación de personaje cancelada.{Colors.ENDC}")
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
            return
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(char_data, f, indent=4, ensure_ascii=False)
    
    print(f"\n{Colors.OKGREEN}{'═' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}✨ ¡Personaje '{char_data['name']}' guardado exitosamente!{Colors.ENDC}")
    print(f"{Colors.GRAY}📁 Ubicación: {file_path}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'═' * 70}{Colors.ENDC}")
    logger.info(f"Personaje creado: {char_data['name']} en {file_path}")
    input(f"\n{Colors.GRAY}Presiona Enter para volver al menú principal...{Colors.ENDC}")


# ============================================================================
# SIMULACIÓN INDIVIDUAL DE DPR
# ============================================================================

def run_individual_simulation():
    """Ejecuta una simulación individual de DPR."""
    clear_screen()
    print_section_header("SIMULACIÓN INDIVIDUAL DE DPR", "⚔️")
    
    try:
        # 1. Seleccionar personaje
        all_characters = _load_all_characters()
        char_names = list(all_characters.keys())
        
        print(f"{Colors.BOLD}{Colors.OKCYAN}Personajes Disponibles:{Colors.ENDC}\n")
        for i, name in enumerate(char_names, 1):
            source = all_characters[name]['source']
            icon = "🏰" if source == "Built-in" else "⭐"
            print(f"{Colors.WARNING}{i}.{Colors.ENDC} {icon} {name} ({source})")
        
        print_separator("─")
        char_idx = get_positive_int_input(
            "Selecciona un personaje",
            default=1,
            min_value=1,
            max_value=len(char_names)
        ) - 1
        
        char_key = char_names[char_idx]
        
        # 2. Nivel
        level = get_positive_int_input(
            "Nivel del personaje",
            default=CombatConstants.DEFAULT_LEVEL,
            min_value=CombatConstants.MIN_LEVEL,
            max_value=CombatConstants.MAX_LEVEL
        )
        
        # 3. Monstruo objetivo
        monster_names = monster_configs.get_all_monster_names()
        print(f"\n{Colors.BOLD}{Colors.FAIL}Monstruos Disponibles (mostrando primeros 20):{Colors.ENDC}")
        for i, name in enumerate(monster_names[:20], 1):
            print(f"{Colors.WARNING}{i}.{Colors.ENDC} {name}")
        
        if len(monster_names) > 20:
            print(f"{Colors.GRAY}... y {len(monster_names) - 20} más{Colors.ENDC}")
        
        print_separator("─")
        monster_name = input(f"{Colors.OKCYAN}Nombre del monstruo objetivo (o 'generic'): {Colors.ENDC}").strip() or "generic"
        
        # 4. Parámetros de simulación
        iterations = get_positive_int_input(
            "Número de iteraciones",
            default=500,
            min_value=1,
            max_value=10000
        )
        
        rounds_per_fight = get_positive_int_input(
            "Rondas por combate",
            default=5,
            min_value=1,
            max_value=100
        )
        
        fights_per_rest = get_positive_int_input(
            "Combates entre descansos largos",
            default=3,
            min_value=1,
            max_value=20
        )
        
        # 5. Ejecutar simulación
        print(f"\n{Colors.BOLD}{Colors.WARNING}⏳ Ejecutando simulación...{Colors.ENDC}\n")
        
        dpr = sim.test_dpr(
            character=configs.CONFIGS[char_key].create(level),
            level=level,
            num_fights=fights_per_rest,
            num_rounds=rounds_per_fight,
            iterations=iterations,
            monster_name=monster_name
        )
        
        # 6. Mostrar resultados
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN}📊 RESULTADOS DE LA SIMULACIÓN{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN}{'═' * 70}{Colors.ENDC}\n")
        
        print(f"Personaje: {Colors.BOLD}{all_characters[char_key]['name']}{Colors.ENDC}")
        print(f"Nivel: {Colors.BOLD}{level}{Colors.ENDC}")
        print(f"Objetivo: {Colors.BOLD}{monster_name}{Colors.ENDC}")
        print(f"Iteraciones: {Colors.BOLD}{iterations}{Colors.ENDC}")
        print(f"\n{Colors.BOLD}{Colors.WARNING}DPR Promedio: {dpr:.2f}{Colors.ENDC}\n")
        
        logger.info(f"Simulación DPR completada: {char_key} nivel {level} = {dpr:.2f} DPR")
        
    except (KeyError, IndexError, ValidationException) as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        logger.error(f"Error en simulación individual: {e}", exc_info=True)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Simulación cancelada{Colors.ENDC}")
    finally:
        input(f"\n{Colors.GRAY}Presiona Enter para volver al menú principal...{Colors.ENDC}")


# ============================================================================
# SIMULACIÓN DE COMBATE DE PARTY
# ============================================================================

def setup_combat_configuration():
    """
    Configura los parámetros del combate interactivo.
    
    Returns:
        CombatConfig o None: Configuración del combate o None si se cancela
    """
    # 1. Nivel
    level = get_positive_int_input(
        "Nivel del combate",
        default=CombatConstants.DEFAULT_LEVEL,
        min_value=CombatConstants.MIN_LEVEL,
        max_value=CombatConstants.MAX_LEVEL
    )
    
    # 2. Seleccionar miembros del party
    print_section_header("SELECCIÓN DE PARTY", "🛡️")
    
    all_characters = _load_all_characters()
    char_names = list(all_characters.keys())
    
    print(f"{Colors.BOLD}{Colors.OKCYAN}Personajes Disponibles:{Colors.ENDC}\n")
    for i, name in enumerate(char_names, 1):
        source = all_characters[name]['source']
        icon = "🏰" if source == "Built-in" else "⭐"
        print(f"{Colors.WARNING}{i}.{Colors.ENDC} {icon} {name} ({source})")
    
    print_separator("─")
    
    party_configs = []
    while True:
        choice = input(f"{Colors.OKCYAN}Selecciona un personaje (o Enter para finalizar): {Colors.ENDC}").strip()
        if not choice:
            break
        
        try:
            char_idx = int(choice) - 1
            if 0 <= char_idx < len(char_names):
                char_key = char_names[char_idx]
                party_configs.append(char_key)
                print(f"{Colors.OKGREEN}✓ Agregado: {char_names[char_idx]}{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Número inválido{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}❌ Entrada inválida{Colors.ENDC}")
    
    if not party_configs:
        print(f"{Colors.FAIL}❌ No se seleccionaron personajes{Colors.ENDC}")
        return None
    
    # 3. Seleccionar enemigos
    print_section_header("SELECCIÓN DE ENEMIGOS", "👹")
    
    enemy_names = monster_configs.get_all_monster_names()
    print(f"{Colors.BOLD}{Colors.FAIL}Monstruos Disponibles (mostrando primeros 30):{Colors.ENDC}\n")
    for i, name in enumerate(enemy_names[:30], 1):
        print(f"{Colors.WARNING}{i}.{Colors.ENDC} 🐉 {name}")
    
    if len(enemy_names) > 30:
        print(f"{Colors.GRAY}... y {len(enemy_names) - 30} más{Colors.ENDC}")
    
    print_separator("─")
    
    enemy_configs_and_counts = []
    while True:
        choice = input(f"{Colors.OKCYAN}Selecciona un enemigo (o Enter para finalizar): {Colors.ENDC}").strip()
        if not choice:
            break
        
        try:
            enemy_idx = int(choice) - 1
            if not (0 <= enemy_idx < len(enemy_names)):
                print(f"{Colors.FAIL}❌ Número inválido{Colors.ENDC}")
                continue
            
            count = get_positive_int_input(
                f"¿Cuántos '{enemy_names[enemy_idx]}' agregar?",
                default=1,
                min_value=1,
                max_value=50
            )
            
            enemy_class = monster_configs.get_monster_class(enemy_names[enemy_idx])
            if enemy_class:
                enemy_configs_and_counts.append((enemy_class, count))
                print(f"{Colors.OKGREEN}✓ Agregados {count}x {enemy_names[enemy_idx]}{Colors.ENDC}")
        except (ValueError, IndexError):
            print(f"{Colors.FAIL}❌ Entrada inválida{Colors.ENDC}")
            continue
    
    if not enemy_configs_and_counts:
        print(f"{Colors.FAIL}❌ No se seleccionaron enemigos{Colors.ENDC}")
        return None
    
    # 4. Número de combates
    num_combats = get_positive_int_input(
        "Número de combates interactivos a ejecutar",
        default=1,
        min_value=1,
        max_value=100
    )
    
    return CombatConfig(
        party_members=party_configs,
        enemies=enemy_configs_and_counts,
        level=level,
        num_combats=num_combats
    )


def execute_interactive_combat(combat, combat_commands):
    """
    Ejecuta un combate interactivo.
    
    Args:
        combat: Instancia de Combat
        combat_commands: Instancia de CombatCommands
    
    Returns:
        bool: True si el combate finalizó normalmente, False si se canceló
    """
    # Setup combat (initiative, etc.)
    if not hasattr(combat, 'turn_order') or not combat.turn_order:
        combat.setup_combat()
    
    all_combatants = combat.party + combat.enemies
    
    while not combat.is_over():
        clear_screen()
        
        # Mostrar estado del combate con barras de HP
        CombatDisplay.show_combat_state_with_bars(combat, combat.rounds)
        
        # Mostrar comandos disponibles
        print(f"{Colors.GRAY}Comandos: inspect <nombre>, c (continuar), summary, save <archivo>, load <archivo>, help, exit{Colors.ENDC}")
        command_str = input(f"\n{Colors.BOLD}{Colors.OKCYAN}👉 Comando: {Colors.ENDC}").strip()
        
        # Parsear comando
        command, args = combat_commands.parse_command(command_str)
        
        if command == 'inspect':
            if not args:
                print(f"{Colors.FAIL}❌ Uso: inspect <nombre del combatiente>{Colors.ENDC}")
                input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
                continue
            
            found_combatant = find_combatant_by_partial_name(args, all_combatants)
            if found_combatant:
                _display_combatant_info(found_combatant)
            else:
                print(f"{Colors.FAIL}❌ Combatiente '{args}' no encontrado{Colors.ENDC}")
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
        
        elif command == 'continue':
            clear_screen()
            print(f"{Colors.BOLD}{Colors.WARNING}▶️  Avanzando a la siguiente acción...{Colors.ENDC}\n")
            combat.run_combat_turn()
        
        elif command == 'summary':
            if hasattr(combat, 'combat_tracker'):
                combat.combat_tracker.print_all_summaries()
            else:
                print(f"{Colors.WARNING}⚠️  No hay tracking de recursos disponible para este combate{Colors.ENDC}")
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
        
        elif command == 'save':
            if not args:
                print(f"{Colors.FAIL}❌ Uso: save <nombre_archivo>{Colors.ENDC}")
            else:
                _save_combat_state(combat, args)
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
        
        elif command == 'load':
            if not args:
                print(f"{Colors.FAIL}❌ Uso: load <nombre_archivo>{Colors.ENDC}")
            else:
                loaded_combat = _load_combat_state(args)
                if loaded_combat:
                    combat = loaded_combat
                    all_combatants = combat.party + combat.enemies
                    print(f"{Colors.OKGREEN}✓ Combate cargado. Continuando desde la ronda {combat.rounds}{Colors.ENDC}")
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
        
        elif command == 'help':
            combat_commands.show_help()
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
        
        elif command == 'exit':
            if prompt_yes_no("¿Realmente quieres salir del combate?", default=False):
                print(f"{Colors.WARNING}⚠️  Combate interactivo terminado{Colors.ENDC}")
                return False
        
        else:
            print(f"{Colors.FAIL}❌ Comando desconocido: '{command_str}'{Colors.ENDC}")
            print(f"{Colors.GRAY}Escribe 'help' para ver los comandos disponibles{Colors.ENDC}")
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
    
    return True


def run_party_simulation():
    """Ejecuta simulación de combate de party - Versión mejorada"""
    clear_screen()
    print_section_header("SIMULACIÓN DE COMBATE DE PARTY", "🗡️")
    
    try:
        # 1. Configurar combate
        config = setup_combat_configuration()
        if config is None:
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
            return
        
        # 2. Validar configuración
        if not validate_combat_config(
            config.party_members,
            config.enemies,
            config.level,
            configs
        ):
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
            return
        
        # 3. Crear gestor de combate
        combat_manager = CombatManager(config, configs, monster_configs, sim.party_sim)
        
        # 4. Crear comandos
        combat_commands = CombatCommands()
        
        # 5. Ejecutar combates
        print(f"\n{Colors.BOLD}{Colors.WARNING}⏳ Preparando combate interactivo...{Colors.ENDC}\n")
        
        results = []
        for i in range(config.num_combats):
            if i > 0:
                print_section_header(f"INICIANDO COMBATE INTERACTIVO #{i+1}", "⚔️")
                input(f"{Colors.GRAY}Presiona Enter para comenzar...{Colors.ENDC}")
            
            # Crear combate
            combat = combat_manager.create_combat()
            
            # Ejecutar combate interactivo
            completed = execute_interactive_combat(combat, combat_commands)
            
            # Si el combate fue completado (no cancelado)
            if completed or combat.is_over():
                result = {
                    'winner': combat._determine_winner() if combat.is_over() else 'cancelled',
                    'rounds': combat.rounds,
                    'final_state': combat.get_final_state()
                }
                results.append(result)
                
                # Mostrar resultado
                clear_screen()
                CombatDisplay.show_combat_result(result, i + 1)
                
                # Mostrar tracker si existe
                if hasattr(combat, 'combat_tracker'):
                    combat.combat_tracker.print_all_summaries()
        
        # 6. Mostrar resumen si hubo múltiples combates
        if len(results) > 1:
            clear_screen()
            CombatDisplay.show_combat_summary(results)
        
        # 7. Ofrecer exportar si hay resultados
        if results and prompt_yes_no("\n¿Exportar resultados?", default=False):
            export_results(results)
        
        logger.info(f"Simulación de party completada: {len(results)} combates")
        
    except SimulatorException as e:
        logger.error(f"Error en simulación: {e}", exc_info=True)
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Simulación cancelada por el usuario{Colors.ENDC}")
    finally:
        input(f"\n{Colors.GRAY}Presiona Enter para volver al menú principal...{Colors.ENDC}")


def export_results(results):
    """
    Exporta resultados de combate a un archivo JSON.
    
    Args:
        results: Lista de resultados de combate
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"combat_results_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"{Colors.OKGREEN}✓ Resultados exportados a {filename}{Colors.ENDC}")
        logger.info(f"Resultados exportados a {filename}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error al exportar: {e}{Colors.ENDC}")
        logger.error(f"Error al exportar resultados: {e}", exc_info=True)


# ============================================================================
# SIMULACIÓN DE PRESETS
# ============================================================================

def run_preset_simulation():
    """Ejecuta una simulación de combate a partir de un preset."""
    clear_screen()
    print_section_header("COMBATE PREDISEÑADO", "📜")

    preset_keys = list(COMBAT_PRESETS.keys())
    preset_options = [f"{COMBAT_PRESETS[key]['name']}" for key in preset_keys]

    print(f"{Colors.BOLD}{Colors.OKCYAN}Elige un escenario:{Colors.ENDC}\n")
    for i, option in enumerate(preset_options, 1):
        key = preset_keys[i-1]
        print(f"{Colors.BOLD}{Colors.WARNING}{i}.{Colors.ENDC} {Colors.WHITE}{option}{Colors.ENDC}")
        print(f"   {Colors.GRAY}{COMBAT_PRESETS[key]['description']}{Colors.ENDC}\n")

    print_separator("─")
    try:
        choice_idx = get_positive_int_input(
            "Elige un preset",
            default=1,
            min_value=1,
            max_value=len(preset_keys)
        ) - 1
        
        selected_key = preset_keys[choice_idx]
        preset = COMBAT_PRESETS[selected_key]
        
        print(f"\n{Colors.OKGREEN}✓ Cargando preset: {preset['name']}{Colors.ENDC}")

        # Convert monster names in preset to monster classes
        enemy_configs_and_counts = []
        for enemy_name, count in preset['enemies']:
            enemy_class = monster_configs.get_monster_class(enemy_name)
            if enemy_class:
                enemy_configs_and_counts.append((enemy_class, count))
            else:
                raise MonsterLoadException(f"No se pudo encontrar la clase de monstruo para '{enemy_name}' en el preset.")

        # Crear configuración de combate desde el preset
        config = CombatConfig(
            party_members=preset['party'],
            enemies=enemy_configs_and_counts,
            level=preset['level'],
            num_combats=1  # Presets are single interactive combats
        )

        # Validar y ejecutar
        if not validate_combat_config(config.party_members, config.enemies, config.level, configs):
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
            return

        combat_manager = CombatManager(config, configs, monster_configs, sim.party_sim)
        combat_commands = CombatCommands()
        
        print(f"\n{Colors.BOLD}{Colors.WARNING}⏳ Preparando combate...{Colors.ENDC}\n")
        input(f"{Colors.GRAY}Presiona Enter para comenzar...{Colors.ENDC}")
        
        combat = combat_manager.create_combat()
        completed = execute_interactive_combat(combat, combat_commands)

        if completed or combat.is_over():
            result = {
                'winner': combat._determine_winner() if combat.is_over() else 'cancelled',
                'rounds': combat.rounds,
                'final_state': combat.get_final_state()
            }
            clear_screen()
            CombatDisplay.show_combat_result(result, 1)
            if hasattr(combat, 'combat_tracker'):
                combat.combat_tracker.print_all_summaries()

    except (SimulatorException, KeyError, IndexError) as e:
        logger.error(f"Error en simulación de preset: {e}", exc_info=True)
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    finally:
        input(f"\n{Colors.GRAY}Presiona Enter para volver al menú principal...{Colors.ENDC}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Loop principal del simulador interactivo."""
    # Crear directorio de personajes personalizados si no existe
    if not os.path.exists(CUSTOM_CHARS_DIR):
        os.makedirs(CUSTOM_CHARS_DIR)
        logger.info(f"Directorio {CUSTOM_CHARS_DIR} creado")
    
    while True:
        try:
            choice = display_main_menu()
            
            if choice == '1':
                run_individual_simulation()
            elif choice == '2':
                run_party_simulation()
            elif choice == '3':
                run_preset_simulation()
            elif choice == '4':
                create_character()
            elif choice == '5':
                clear_screen()
                print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'═' * 70}")
                print(f"  ⚔️  ¡Gracias por usar el D&D 5e Damage Simulator!  🎲")
                print(f"  {'═' * 70}{Colors.ENDC}\n")
                print(f"{Colors.OKCYAN}  ¡Que tus dados siempre rueden a tu favor!{Colors.ENDC}\n")
                logger.info("Aplicación cerrada normalmente")
                break
            else:
                print(f"{Colors.FAIL}❌ Opción inválida, por favor intenta de nuevo.{Colors.ENDC}")
                input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}⚠️  Interrumpido por el usuario{Colors.ENDC}")
            if prompt_yes_no("¿Salir del simulador?", default=True):
                logger.info("Aplicación cerrada por interrupción de usuario")
                break
        except Exception as e:
            logger.error(f"Error inesperado: {e}", exc_info=True)
            print(f"\n{Colors.FAIL}❌ Error inesperado: {e}{Colors.ENDC}")
            if not prompt_yes_no("¿Continuar usando el simulador?", default=True):
                break


if __name__ == "__main__":
    main()
