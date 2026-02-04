"""
Constantes para el simulador D&D 5e.
"""


class CombatConstants:
    """Constantes relacionadas con combate"""
    MAX_COMBAT_ROUNDS = 100
    DEFAULT_ITERATIONS = 1
    MIN_LEVEL = 1
    MAX_LEVEL = 20
    DEFAULT_LEVEL = 5


class UIConstants:
    """Constantes de interfaz de usuario"""
    SEPARATOR_LENGTH = 70
    SEPARATOR_CHAR = "═"
    TABLE_ALIGN = "l"
    HP_BAR_LENGTH = 20


class SimulationConstants:
    """Constantes de simulación"""
    DEFAULT_ROUNDS_PER_FIGHT = 5
    DEFAULT_FIGHTS_PER_REST = 3
    DEFAULT_ITERATIONS = 500
    MAX_ITERATIONS = 10000


# Directorio para personajes personalizados
CUSTOM_CHARS_DIR = "custom_chars"
