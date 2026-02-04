# 🎯 Recomendaciones de Mejora para `interactive_sim.py`

Análisis completo del código con sugerencias de refactorización, optimización y mejores prácticas.

---

## 📋 Índice

1. [Errores Críticos Corregidos](#errores-críticos-corregidos)
2. [Arquitectura y Organización](#arquitectura-y-organización)
3. [Mejoras de Usabilidad](#mejoras-de-usabilidad)
4. [Optimizaciones de Rendimiento](#optimizaciones-de-rendimiento)
5. [Manejo de Errores](#manejo-de-errores)
6. [Mejoras de Interfaz](#mejoras-de-interfaz)
7. [Funcionalidades Adicionales](#funcionalidades-adicionales)

---

## 🔧 Errores Críticos Corregidos

### 1. **Constructor de Monstruos** ✅
**Problema:** Los monstruos no aceptan `level` como parámetro
```python
# ❌ ANTES
enemy_instances.append(enemy_class(level=level))

# ✅ AHORA
enemy_instances.append(enemy_class())
```

### 2. **Parámetros de Combat** ✅
**Problema:** Nombres incorrectos de parámetros
```python
# ❌ ANTES
combat = sim.party_sim.Combat(
    party_instances=party_instances,
    monster_instances=enemy_instances
)

# ✅ AHORA
combat = sim.party_sim.Combat(
    party=party_instances,
    monsters=enemy_instances
)
```

---

## 🏗️ Arquitectura y Organización

### 1. **Separar Lógica de Presentación**

**Problema Actual:** La lógica de negocio está mezclada con la UI

**Solución Recomendada:**
```python
# Crear archivo: ui/combat_display.py
class CombatDisplay:
    """Maneja toda la visualización del combate"""
    
    @staticmethod
    def show_combatant_status(combatants):
        """Muestra el estado actual de todos los combatientes"""
        table = PrettyTable()
        table.field_names = ["Combatiente", "Equipo", "HP", "Estado"]
        # ... lógica de visualización
        return table
    
    @staticmethod
    def show_combat_summary(combat_result):
        """Muestra resumen del combate"""
        # ... lógica de resumen

# Crear archivo: logic/combat_manager.py
class CombatManager:
    """Gestiona la lógica del combate"""
    
    def __init__(self, party_configs, enemy_configs, level):
        self.party_configs = party_configs
        self.enemy_configs = enemy_configs
        self.level = level
        
    def create_party_instances(self):
        """Crea instancias del party"""
        # ... lógica de creación
        
    def create_enemy_instances(self):
        """Crea instancias de enemigos"""
        # ... lógica de creación
```

### 2. **Usar DataClasses para Configuración**

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CombatConfig:
    """Configuración para un combate"""
    party_members: List[str]
    enemies: List[tuple]  # (enemy_class, count)
    level: int
    num_combats: int = 1
    
@dataclass
class SimulationSettings:
    """Configuración global de simulación"""
    iterations: int = 500
    rounds_per_fight: int = 5
    fights_per_rest: int = 3
    monster_name: str = "generic"
```

### 3. **Constantes Globales**

```python
# constants.py
class CombatConstants:
    MAX_COMBAT_ROUNDS = 100
    DEFAULT_ITERATIONS = 1
    MIN_LEVEL = 1
    MAX_LEVEL = 20
    
class UIConstants:
    SEPARATOR_LENGTH = 70
    SEPARATOR_CHAR = "═"
    TABLE_ALIGN = "l"
```

---

## 🎨 Mejoras de Usabilidad

### 1. **Sistema de Comandos Mejorado**

**Problema:** Los comandos están hardcodeados y dispersos

**Solución:**
```python
class CombatCommand:
    """Representa un comando disponible en combate"""
    def __init__(self, name, aliases, description, handler):
        self.name = name
        self.aliases = aliases
        self.description = description
        self.handler = handler

class CombatCommands:
    """Gestor de comandos de combate"""
    def __init__(self):
        self.commands = {
            'inspect': CombatCommand(
                name='inspect',
                aliases=['i', 'info'],
                description='Inspeccionar un combatiente',
                handler=self.handle_inspect
            ),
            'continue': CombatCommand(
                name='continue',
                aliases=['c', 'next'],
                description='Avanzar a la siguiente acción',
                handler=self.handle_continue
            ),
            # ... más comandos
        }
    
    def show_help(self):
        """Muestra todos los comandos disponibles"""
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}📖 COMANDOS DISPONIBLES{Colors.ENDC}\n")
        for cmd in self.commands.values():
            aliases_str = ", ".join(cmd.aliases)
            print(f"  {Colors.WARNING}{cmd.name}{Colors.ENDC} ({aliases_str})")
            print(f"    {Colors.GRAY}{cmd.description}{Colors.ENDC}")
```

### 2. **Autocompletado de Nombres**

```python
def find_combatant_by_partial_name(name_partial: str, combatants: List) -> Optional[Combatant]:
    """Encuentra un combatiente por nombre parcial"""
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
```

### 3. **Historial de Acciones**

```python
class CombatHistory:
    """Rastrea el historial del combate"""
    def __init__(self):
        self.actions = []
        self.round_summaries = {}
    
    def add_action(self, round_num, actor, action, target=None, result=None):
        """Registra una acción"""
        self.actions.append({
            'round': round_num,
            'actor': actor,
            'action': action,
            'target': target,
            'result': result,
            'timestamp': time.time()
        })
    
    def get_round_summary(self, round_num):
        """Obtiene resumen de una ronda"""
        return [a for a in self.actions if a['round'] == round_num]
    
    def show_last_actions(self, count=5):
        """Muestra las últimas N acciones"""
        for action in self.actions[-count:]:
            print(f"Ronda {action['round']}: {action['actor']} -> {action['action']}")
```

---

## ⚡ Optimizaciones de Rendimiento

### 1. **Caché de Instancias**

```python
class EntityCache:
    """Cache para instancias de personajes y monstruos"""
    def __init__(self):
        self._party_cache = {}
        self._monster_cache = {}
    
    def get_party_member(self, config_key, level):
        """Obtiene o crea una instancia de party member"""
        cache_key = f"{config_key}_{level}"
        if cache_key not in self._party_cache:
            constructor = configs.CLASS_REGISTRY.get(config_key)
            if constructor:
                self._party_cache[cache_key] = constructor(level=level)
        
        # Devuelve una copia para evitar modificar el cache
        return self._party_cache[cache_key].copy() if cache_key in self._party_cache else None
    
    def get_monster(self, monster_class):
        """Obtiene o crea una instancia de monstruo"""
        class_name = monster_class.__name__
        if class_name not in self._monster_cache:
            self._monster_cache[class_name] = monster_class()
        
        return self._monster_cache[class_name].copy()
```

### 2. **Validación de Entrada Temprana**

```python
def validate_combat_setup(party_configs, enemy_configs, level):
    """Valida la configuración antes de crear instancias"""
    errors = []
    
    # Validar level
    if not (1 <= level <= 20):
        errors.append(f"Nivel inválido: {level}. Debe estar entre 1 y 20.")
    
    # Validar party
    if not party_configs:
        errors.append("El party no puede estar vacío.")
    
    for config in party_configs:
        if config not in configs.CONFIGS and not os.path.exists(f"{CUSTOM_CHARS_DIR}/{config}.json"):
            errors.append(f"Configuración de personaje no encontrada: {config}")
    
    # Validar enemies
    if not enemy_configs:
        errors.append("Debe haber al menos un enemigo.")
    
    for enemy_class, count in enemy_configs:
        if count < 1:
            errors.append(f"El conteo de enemigos debe ser positivo: {count}")
    
    if errors:
        print(f"{Colors.FAIL}❌ ERRORES DE VALIDACIÓN:{Colors.ENDC}")
        for error in errors:
            print(f"  • {error}")
        return False
    
    return True
```

---

## 🛡️ Manejo de Errores

### 1. **Excepciones Personalizadas**

```python
# exceptions.py
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
```

### 2. **Manejo Robusto de Errores**

```python
def safe_load_character(char_key, level):
    """Carga un personaje con manejo de errores robusto"""
    try:
        # Intentar cargar desde configs
        if char_key in configs.CONFIGS:
            return configs.CONFIGS[char_key].create(level)
        
        # Intentar cargar desde custom
        custom_path = os.path.join(CUSTOM_CHARS_DIR, f"{char_key}.json")
        if os.path.exists(custom_path):
            with open(custom_path, 'r') as f:
                char_data = json.load(f)
                constructor = configs.CLASS_REGISTRY.get(char_data.get("class"))
                if constructor:
                    return constructor(level=level, **char_data.get('args', {}))
                else:
                    raise CharacterLoadException(f"Clase no encontrada: {char_data.get('class')}")
        
        raise CharacterLoadException(f"Personaje no encontrado: {char_key}")
        
    except json.JSONDecodeError as e:
        raise CharacterLoadException(f"Error al parsear JSON para {char_key}: {e}")
    except KeyError as e:
        raise CharacterLoadException(f"Clave faltante en configuración de {char_key}: {e}")
    except Exception as e:
        raise CharacterLoadException(f"Error inesperado al cargar {char_key}: {e}")
```

### 3. **Logging Estructurado**

```python
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'combat_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('interactive_sim')

# Uso
logger.info(f"Iniciando combate: {len(party)} vs {len(enemies)}")
logger.warning(f"Personaje {char_name} tiene HP bajo: {hp}/{max_hp}")
logger.error(f"Error al cargar monstruo: {monster_name}", exc_info=True)
```

---

## 💅 Mejoras de Interfaz

### 1. **Barra de Progreso**

```python
from tqdm import tqdm

def run_multiple_combats(combat_config, num_combats):
    """Ejecuta múltiples combates con barra de progreso"""
    results = []
    
    with tqdm(total=num_combats, desc="Combates", ncols=100) as pbar:
        for i in range(num_combats):
            combat = create_combat(combat_config)
            result = combat.run_combat()
            results.append(result)
            pbar.update(1)
            pbar.set_postfix({
                'Ganados': sum(1 for r in results if r['winner'] == 'party'),
                'Rondas Prom': sum(r['rounds'] for r in results) / len(results)
            })
    
    return results
```

### 2. **Gráficos de HP**

```python
def display_hp_bars(combatants):
    """Muestra barras visuales de HP"""
    for combatant in combatants:
        entity = combatant.entity
        hp_percent = (entity.hp / entity.max_hp) * 100
        
        # Determinar color basado en % de HP
        if hp_percent > 75:
            color = Colors.OKGREEN
        elif hp_percent > 50:
            color = Colors.WARNING
        elif hp_percent > 25:
            color = Colors.FAIL
        else:
            color = Colors.MAGENTA
        
        # Crear barra visual
        bar_length = 20
        filled = int(bar_length * hp_percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"{entity.name:20s} [{color}{bar}{Colors.ENDC}] {entity.hp}/{entity.max_hp} ({hp_percent:.0f}%)")
```

### 3. **Menú Interactivo con Números**

```python
def select_from_menu(title, options, allow_multiple=False):
    """Muestra un menú y permite seleccionar opciones"""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{title}{Colors.ENDC}\n")
    
    for i, option in enumerate(options, 1):
        print(f"{Colors.WARNING}{i}.{Colors.ENDC} {option}")
    
    print_separator("─")
    
    if allow_multiple:
        prompt = "Selecciona opciones (ej: 1,3,5 o 'todos'): "
    else:
        prompt = f"Selecciona una opción (1-{len(options)}): "
    
    while True:
        choice = input(f"{Colors.OKCYAN}{prompt}{Colors.ENDC}").strip()
        
        if allow_multiple and choice.lower() == 'todos':
            return list(range(len(options)))
        
        try:
            if allow_multiple and ',' in choice:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                if all(0 <= i < len(options) for i in indices):
                    return indices
            else:
                index = int(choice) - 1
                if 0 <= index < len(options):
                    return [index] if allow_multiple else index
            
            print(f"{Colors.FAIL}❌ Selección inválida. Intenta de nuevo.{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}❌ Entrada inválida. Usa números separados por comas.{Colors.ENDC}")
```

---

## 🚀 Funcionalidades Adicionales

### 1. **Exportar Resultados**

```python
import json
import csv
from datetime import datetime

class ResultsExporter:
    """Exporta resultados de combate a varios formatos"""
    
    @staticmethod
    def to_json(combat_results, filename=None):
        """Exporta a JSON"""
        if filename is None:
            filename = f"combat_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(combat_results, f, indent=2, ensure_ascii=False)
        
        print(f"{Colors.OKGREEN}✓ Resultados exportados a {filename}{Colors.ENDC}")
    
    @staticmethod
    def to_csv(combat_results, filename=None):
        """Exporta a CSV"""
        if filename is None:
            filename = f"combat_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Combat', 'Winner', 'Rounds', 'Party_Survivors', 'Enemy_Survivors'])
            
            for i, result in enumerate(combat_results, 1):
                party_alive = sum(1 for c in result['final_state'] if c['team'] == 'party' and c['status'] == 'alive')
                enemy_alive = sum(1 for c in result['final_state'] if c['team'] == 'enemies' and c['status'] == 'alive')
                writer.writerow([i, result['winner'], result['rounds'], party_alive, enemy_alive])
        
        print(f"{Colors.OKGREEN}✓ Resultados exportados a {filename}{Colors.ENDC}")
```

### 2. **Estadísticas Avanzadas**

```python
class CombatStatistics:
    """Calcula estadísticas detalladas de combates"""
    
    def __init__(self, combat_results):
        self.results = combat_results
    
    def win_rate(self):
        """Tasa de victoria del party"""
        wins = sum(1 for r in self.results if r['winner'] == 'party')
        return (wins / len(self.results)) * 100 if self.results else 0
    
    def average_rounds(self):
        """Promedio de rondas por combate"""
        return sum(r['rounds'] for r in self.results) / len(self.results) if self.results else 0
    
    def average_survivors(self, team='party'):
        """Promedio de sobrevivientes por equipo"""
        total = 0
        for result in self.results:
            survivors = sum(1 for c in result['final_state'] 
                          if c['team'] == team and c['status'] == 'alive')
            total += survivors
        return total / len(self.results) if self.results else 0
    
    def round_distribution(self):
        """Distribución de duración de combates"""
        from collections import Counter
        return Counter(r['rounds'] for r in self.results)
    
    def print_summary(self):
        """Imprime un resumen completo"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN}📊 ESTADÍSTICAS DE COMBATE{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'═' * 70}{Colors.ENDC}\n")
        
        print(f"Total de combates: {Colors.BOLD}{len(self.results)}{Colors.ENDC}")
        print(f"Tasa de victoria: {Colors.BOLD}{self.win_rate():.1f}%{Colors.ENDC}")
        print(f"Rondas promedio: {Colors.BOLD}{self.average_rounds():.1f}{Colors.ENDC}")
        print(f"Sobrevivientes promedio (Party): {Colors.BOLD}{self.average_survivors('party'):.1f}{Colors.ENDC}")
        print(f"Sobrevivientes promedio (Enemigos): {Colors.BOLD}{self.average_survivors('enemies'):.1f}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Distribución de duración:{Colors.ENDC}")
        for rounds, count in sorted(self.round_distribution().items()):
            bar = "█" * int(count / len(self.results) * 50)
            print(f"  {rounds:2d} rondas: {bar} ({count})")
```

### 3. **Replay de Combate**

```python
class CombatRecorder:
    """Graba y reproduce combates"""
    
    def __init__(self):
        self.frames = []
        self.current_frame = 0
    
    def record_frame(self, combat_state):
        """Graba un frame del combate"""
        self.frames.append({
            'round': combat_state.rounds,
            'combatants': [(c.entity.name, c.entity.hp, c.entity.max_hp) 
                          for c in combat_state.combatants],
            'turn_order': [c.entity.name for c in combat_state.turn_order]
        })
    
    def save_to_file(self, filename):
        """Guarda la grabación a archivo"""
        with open(filename, 'wb') as f:
            pickle.dump(self.frames, f)
    
    def load_from_file(self, filename):
        """Carga una grabación"""
        with open(filename, 'rb') as f:
            self.frames = pickle.load(f)
        self.current_frame = 0
    
    def play(self):
        """Reproduce el combate grabado"""
        for frame in self.frames:
            clear_screen()
            print(f"Ronda {frame['round']}")
            for name, hp, max_hp in frame['combatants']:
                print(f"{name}: {hp}/{max_hp}")
            input("Presiona Enter para siguiente frame...")
```

### 4. **Presets de Combate**

```python
# combat_presets.py
COMBAT_PRESETS = {
    "tutorial": {
        "name": "Tutorial: 4 vs 4 Goblins",
        "party": ["fighter", "wizard", "rogue", "cleric"],
        "enemies": [("goblin", 4)],
        "level": 1,
        "description": "Combate básico para aprender los controles"
    },
    "boss_fight": {
        "name": "Jefe: Dragón Adulto",
        "party": ["paladin", "wizard", "cleric", "ranger"],
        "enemies": [("adult_red_dragon", 1)],
        "level": 10,
        "description": "Combate épico contra un dragón"
    },
    "horde": {
        "name": "Horda: Invasión de Zombies",
        "party": ["fighter", "fighter", "cleric", "wizard"],
        "enemies": [("zombie", 20)],
        "level": 5,
        "description": "Defiende contra una horda"
    },
    # ... más presets
}

def load_preset(preset_name):
    """Carga un preset de combate"""
    if preset_name not in COMBAT_PRESETS:
        print(f"{Colors.FAIL}❌ Preset no encontrado: {preset_name}{Colors.ENDC}")
        return None
    
    preset = COMBAT_PRESETS[preset_name]
    print(f"{Colors.OKGREEN}✓ Cargando preset: {preset['name']}{Colors.ENDC}")
    print(f"{Colors.GRAY}{preset['description']}{Colors.ENDC}")
    
    return preset
```

---

## 📝 Código Refactorizado Ejemplo

### Estructura Mejorada de `run_party_simulation()`

```python
def run_party_simulation():
    """Ejecuta simulación de combate de party - Versión mejorada"""
    clear_screen()
    print_section_header("SIMULACIÓN DE COMBATE DE PARTY", "🗡️")
    
    try:
        # 1. Configurar combate
        config = setup_combat_configuration()
        if config is None:
            return
        
        # 2. Validar configuración
        if not validate_combat_setup(config):
            input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.ENDC}")
            return
        
        # 3. Crear instancias
        combat_manager = CombatManager(config)
        combat = combat_manager.create_combat()
        
        # 4. Ejecutar combates
        results = execute_interactive_combats(combat, config.num_combats)
        
        # 5. Mostrar estadísticas
        stats = CombatStatistics(results)
        stats.print_summary()
        
        # 6. Ofrecer exportar
        if prompt_yes_no("¿Exportar resultados?"):
            export_format = select_from_menu("Formato de exportación", ["JSON", "CSV"])
            if export_format == 0:
                ResultsExporter.to_json(results)
            else:
                ResultsExporter.to_csv(results)
    
    except SimulatorException as e:
        logger.error(f"Error en simulación: {e}", exc_info=True)
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Simulación cancelada por el usuario{Colors.ENDC}")
    finally:
        input(f"\n{Colors.GRAY}Presiona Enter para volver al menú principal...{Colors.ENDC}")

def setup_combat_configuration():
    """Configura los parámetros del combate"""
    # Nivel
    level = get_level_input()
    if level is None:
        return None
    
    # Party
    party_configs = select_party_members()
    if not party_configs:
        return None
    
    # Enemigos
    enemy_configs = select_enemies()
    if not enemy_configs:
        return None
    
    # Número de combates
    num_combats = get_positive_int_input(
        "Número de combates interactivos a ejecutar",
        default=1,
        min_value=1,
        max_value=100
    )
    
    return CombatConfig(
        party_members=party_configs,
        enemies=enemy_configs,
        level=level,
        num_combats=num_combats
    )

def get_positive_int_input(prompt, default=1, min_value=1, max_value=None):
    """Obtiene input de entero positivo con validación"""
    while True:
        try:
            value = input(f"\n{Colors.OKCYAN}{prompt} (default: {default}): {Colors.ENDC}").strip()
            if not value:
                return default
            
            value = int(value)
            if value < min_value:
                print(f"{Colors.FAIL}❌ Valor debe ser al menos {min_value}{Colors.ENDC}")
                continue
            if max_value and value > max_value:
                print(f"{Colors.FAIL}❌ Valor no puede exceder {max_value}{Colors.ENDC}")
                continue
            
            return value
        except ValueError:
            print(f"{Colors.FAIL}❌ Por favor ingresa un número válido{Colors.ENDC}")
```

---

## 🎯 Prioridades de Implementación

### Alta Prioridad (Implementar Primero)
1. ✅ Corregir errores críticos (YA HECHO)
2. Separar lógica de presentación
3. Mejorar manejo de errores
4. Validación de entrada temprana

### Media Prioridad
5. Sistema de comandos mejorado
6. Autocompletado de nombres
7. Estadísticas avanzadas
8. Exportar resultados

### Baja Prioridad (Nice to Have)
9. Barra de progreso
10. Gráficos de HP
11. Replay de combate
12. Presets de combate

---

## 📚 Recursos Adicionales

### Testing
```python
# tests/test_combat.py
import unittest
from interactive_sim import CombatManager, CombatConfig

class TestCombatManager(unittest.TestCase):
    def test_create_party_instances(self):
        """Verifica creación correcta de party"""
        config = CombatConfig(
            party_members=["fighter", "wizard"],
            enemies=[("goblin", 2)],
            level=5
        )
        manager = CombatManager(config)
        party = manager.create_party_instances()
        
        self.assertEqual(len(party), 2)
        self.assertEqual(party[0].level, 5)
    
    def test_invalid_level(self):
        """Verifica que niveles inválidos fallen"""
        with self.assertRaises(ValueError):
            CombatConfig(
                party_members=["fighter"],
                enemies=[("goblin", 1)],
                level=25  # Inválido
            )
```

### Documentación
```python
def create_combat(config: CombatConfig) -> Combat:
    """
    Crea una instancia de Combat a partir de una configuración.
    
    Args:
        config: Configuración del combate con party, enemigos y nivel
    
    Returns:
        Combat: Instancia de combate lista para ejecutar
    
    Raises:
        InvalidConfigException: Si la configuración es inválida
        CharacterLoadException: Si no se puede cargar un personaje
        MonsterLoadException: Si no se puede cargar un monstruo
    
    Example:
        >>> config = CombatConfig(
        ...     party_members=["fighter", "wizard"],
        ...     enemies=[("goblin", 4)],
        ...     level=3
        ... )
        >>> combat = create_combat(config)
        >>> result = combat.run_combat()
    """
    # Implementación...
```

---

## 🏁 Conclusión

Estas mejoras transformarán `interactive_sim.py` de un script funcional a una aplicación robusta, mantenible y escalable. La clave está en implementarlas gradualmente, comenzando por las de alta prioridad.

### Beneficios Esperados:
- ✅ **Menos errores** gracias a validación temprana
- ✅ **Código más limpio** con separación de responsabilidades  
- ✅ **Mejor UX** con comandos mejorados y feedback claro
- ✅ **Más funcionalidades** como exportación y estadísticas
- ✅ **Más fácil de mantener** con arquitectura modular

### Siguiente Paso Recomendado:
Empezar creando los módulos separados (ui/, logic/, exceptions.py) y mover gradualmente la funcionalidad existente a la nueva estructura.
