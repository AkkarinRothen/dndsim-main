"""
Excepciones personalizadas para el simulador D&D 5e.
"""


class SimulatorException(Exception):
    """Excepción base para el simulador"""
    pass


class InvalidConfigException(SimulatorException):
    """Configuración inválida"""
    pass


class CombatSetupException(SimulatorException):
    """Error al configurar el combate"""
    pass


class CharacterLoadException(SimulatorException):
    """Error al cargar un personaje"""
    pass


class MonsterLoadException(SimulatorException):
    """Error al cargar un monstruo"""
    pass


class ValidationException(SimulatorException):
    """Error de validación de entrada"""
    pass
