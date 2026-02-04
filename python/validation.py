"""
Funciones de validación para configuraciones de combate.
"""
import os
from constants import CombatConstants, CUSTOM_CHARS_DIR
from simulator_exceptions import ValidationException
from colors import Colors


def validate_level(level):
    """
    Valida que el nivel esté en el rango correcto.
    
    Args:
        level: Nivel a validar
    
    Raises:
        ValidationException: Si el nivel es inválido
    
    Returns:
        int: Nivel validado
    """
    if not isinstance(level, int):
        raise ValidationException(f"El nivel debe ser un entero, recibido: {type(level).__name__}")
    
    if not (CombatConstants.MIN_LEVEL <= level <= CombatConstants.MAX_LEVEL):
        raise ValidationException(
            f"Nivel inválido: {level}. Debe estar entre {CombatConstants.MIN_LEVEL} y {CombatConstants.MAX_LEVEL}."
        )
    
    return level


def validate_party_configs(party_configs, configs_module):
    """
    Valida las configuraciones del party.
    
    Args:
        party_configs: Lista de configuraciones de personajes
        configs_module: Módulo configs para verificar existencia
    
    Raises:
        ValidationException: Si alguna configuración es inválida
    
    Returns:
        List[str]: Configuraciones validadas
    """
    errors = []
    
    if not party_configs:
        errors.append("El party no puede estar vacío.")
    
    for config_key in party_configs:
        # Verificar si existe en configs built-in
        if config_key in configs_module.CONFIGS:
            continue
        
        # Verificar si existe en custom chars
        custom_path = os.path.join(CUSTOM_CHARS_DIR, f"{config_key}.json")
        if os.path.exists(custom_path):
            continue
        
        errors.append(f"Configuración de personaje no encontrada: {config_key}")
    
    if errors:
        raise ValidationException("\n".join(errors))
    
    return party_configs


def validate_enemy_configs(enemy_configs):
    """
    Valida las configuraciones de enemigos.
    
    Args:
        enemy_configs: Lista de tuplas (enemy_class, count)
    
    Raises:
        ValidationException: Si alguna configuración es inválida
    
    Returns:
        List[tuple]: Configuraciones validadas
    """
    errors = []
    
    if not enemy_configs:
        errors.append("Debe haber al menos un enemigo.")
    
    for enemy_class, count in enemy_configs:
        if not isinstance(count, int) or count < 1:
            errors.append(f"El conteo de enemigos debe ser un entero positivo: {count}")
        
        if not callable(enemy_class):
            errors.append(f"Clase de enemigo inválida: {enemy_class}")
    
    if errors:
        raise ValidationException("\n".join(errors))
    
    return enemy_configs


def validate_combat_config(party_configs, enemy_configs, level, configs_module):
    """
    Valida la configuración completa del combate.
    
    Args:
        party_configs: Lista de configuraciones de personajes
        enemy_configs: Lista de tuplas (enemy_class, count)
        level: Nivel del combate
        configs_module: Módulo configs
    
    Returns:
        bool: True si la validación es exitosa
    """
    try:
        validate_level(level)
        validate_party_configs(party_configs, configs_module)
        validate_enemy_configs(enemy_configs)
        return True
    
    except ValidationException as e:
        print(f"{Colors.FAIL}❌ ERRORES DE VALIDACIÓN:{Colors.ENDC}")
        for error in str(e).split('\n'):
            print(f"  • {error}")
        return False


def find_combatant_by_partial_name(name_partial, combatants):
    """
    Encuentra un combatiente por nombre parcial.
    
    Args:
        name_partial: Nombre parcial a buscar
        combatants: Lista de combatientes
    
    Returns:
        Combatant o None: Combatiente encontrado o None si no hay match único
    """
    name_partial = name_partial.lower()
    
    # Búsqueda exacta primero
    for c in combatants:
        if c.entity.name.lower() == name_partial:
            return c
    
    # Búsqueda por comienzo
    matches = [c for c in combatants if c.entity.name.lower().startswith(name_partial)]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"{Colors.WARNING}⚠️  Múltiples coincidencias: {', '.join(c.entity.name for c in matches)}{Colors.ENDC}")
        return None
    
    # Búsqueda por contiene
    matches = [c for c in combatants if name_partial in c.entity.name.lower()]
    if len(matches) == 1:
        return matches[0]
    
    return None
