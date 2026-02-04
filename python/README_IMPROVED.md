# D&D 5e Interactive Simulator - Versión Mejorada

## 🎯 Descripción

Simulador interactivo de combate para D&D 5e completamente refactorizado con mejoras en arquitectura, usabilidad, manejo de errores y funcionalidades.

## 📦 Archivos del Proyecto

### Archivo Principal
- **`interactive_sim_improved.py`** - Archivo principal del simulador mejorado

### Módulos de Soporte
- **`colors.py`** - Constantes de colores ANSI para la terminal
- **`constants.py`** - Constantes globales del simulador
- **`simulator_exceptions.py`** - Excepciones personalizadas
- **`ui_utils.py`** - Utilidades de interfaz de usuario
- **`validation.py`** - Funciones de validación
- **`combat_display.py`** - Clases para visualización de combates
- **`combat_manager.py`** - Gestión de lógica de combate

## 🚀 Instalación

### Requisitos Previos
```bash
pip install prettytable
```

### Estructura de Archivos
Coloca todos los archivos en el mismo directorio que tu proyecto existente:

```
tu_proyecto/
├── interactive_sim_improved.py  # Nuevo archivo principal
├── colors.py                     # Nuevo módulo
├── constants.py                  # Nuevo módulo
├── simulator_exceptions.py       # Nuevo módulo
├── ui_utils.py                   # Nuevo módulo
├── validation.py                 # Nuevo módulo
├── combat_display.py             # Nuevo módulo
├── combat_manager.py             # Nuevo módulo
├── configs.py                    # Existente
├── monster_configs.py            # Existente
├── sim/                          # Existente
│   ├── __init__.py
│   ├── party_sim.py
│   ├── character.py
│   └── monster.py
└── custom_chars/                 # Se crea automáticamente
```

## 💡 Uso

### Ejecutar el Simulador
```bash
python interactive_sim_improved.py
```

### Menú Principal
Al ejecutar, verás 4 opciones:

1. **Simulación Individual de DPR**
   - Calcula el daño promedio por ronda de un personaje
   - Configurable: nivel, objetivo, iteraciones

2. **Simulación de Combate de Party**
   - Combate interactivo completo
   - Selecciona party y enemigos
   - Controla el combate turno por turno

3. **Crear Nuevo Personaje**
   - Diseña personajes personalizados
   - Guarda en `custom_chars/`

4. **Salir**

## 🎮 Comandos de Combate Interactivo

Durante un combate, puedes usar estos comandos:

| Comando | Alias | Descripción |
|---------|-------|-------------|
| `inspect <nombre>` | `i`, `info` | Inspeccionar un combatiente |
| `continue` | `c`, `next` | Avanzar a la siguiente acción |
| `summary` | `s`, `stats` | Mostrar resumen del combate |
| `save <archivo>` | - | Guardar estado del combate |
| `load <archivo>` | - | Cargar estado del combate |
| `help` | `h`, `?` | Mostrar ayuda |
| `exit` | `quit`, `q` | Salir del combate |

### Ejemplos de Uso
```
👉 Comando: inspect Goblin 1
👉 Comando: c
👉 Comando: save mi_combate
👉 Comando: help
```

## ✨ Mejoras Implementadas

### 1. Arquitectura Modular
- ✅ Separación de lógica de presentación
- ✅ Módulos especializados por responsabilidad
- ✅ Código más mantenible y testeable

### 2. Manejo de Errores Robusto
- ✅ Excepciones personalizadas
- ✅ Validación temprana de entrada
- ✅ Mensajes de error claros
- ✅ Logging estructurado

### 3. Mejoras de UI
- ✅ Barras visuales de HP
- ✅ Sistema de comandos mejorado con alias
- ✅ Búsqueda inteligente de combatientes por nombre parcial
- ✅ Confirmaciones para acciones destructivas
- ✅ Ayuda contextual con comando `help`

### 4. Funcionalidades Nuevas
- ✅ Guardar/cargar estado de combate
- ✅ Exportar resultados a JSON
- ✅ Resumen de múltiples combates
- ✅ Visualización mejorada con colores

### 5. Calidad de Código
- ✅ Type hints en funciones críticas
- ✅ Docstrings completos
- ✅ Constantes globales en lugar de magic numbers
- ✅ Logging para debugging

## 🐛 Bugs Corregidos

### Críticos
1. ✅ **Constructor de Monstruos**
   - Antes: `enemy_class(level=level)` ❌
   - Ahora: `enemy_class()` ✅

2. ✅ **Parámetros de Combat**
   - Antes: `Combat(party_instances=..., monster_instances=...)` ❌
   - Ahora: `Combat(party=..., enemies=...)` ✅

## 📊 Ejemplo de Sesión

```
╔═══════════════════════════════════════════════════════════════════╗
║  ⚔️  🎲  D&D 5E DAMAGE SIMULATOR  🎲  ⚔️                          ║
╚═══════════════════════════════════════════════════════════════════╝

📋 MENÚ PRINCIPAL

1. ⚔️  Simulación Individual de DPR
   Calcula el daño por round de personajes

2. 🗡️  Simulación de Combate de Party
   Simula batallas completas de grupo

👉 Elige una opción: 2

──────────────────────────────────────────────────────────────────
                    🗡️  SIMULACIÓN DE COMBATE DE PARTY
──────────────────────────────────────────────────────────────────

🔢 Nivel del combate (default: 5): 3

──────────────────────────────────────────────────────────────────
                       🛡️  SELECCIÓN DE PARTY
──────────────────────────────────────────────────────────────────

Personajes Disponibles:

1. 🏰 fighter (Built-in)
2. 🏰 wizard (Built-in)
3. 🏰 cleric (Built-in)

👉 Selecciona un personaje (o Enter para finalizar): 1
✓ Agregado: fighter

👉 Selecciona un personaje (o Enter para finalizar): 2
✓ Agregado: wizard

👉 Selecciona un personaje (o Enter para finalizar): 

──────────────────────────────────────────────────────────────────
                      👹 SELECCIÓN DE ENEMIGOS
──────────────────────────────────────────────────────────────────

1. 🐉 goblin
2. 🐉 orc

👉 Selecciona un enemigo (o Enter para finalizar): 1

🔢 ¿Cuántos 'goblin' agregar? (default: 1): 4
✓ Agregados 4x goblin

──────────────────────────────────────────────────────────────────
                            🔄 RONDA 1
──────────────────────────────────────────────────────────────────

🛡️  PARTY
Fighter              [████████████████████] 30/30 (100%)
Wizard               [████████████████████] 18/18 (100%)

👹 ENEMIGOS
Goblin 1             [████████████████████] 7/7 (100%)
Goblin 2             [████████████████████] 7/7 (100%)
Goblin 3             [████████████████████] 7/7 (100%)
Goblin 4             [████████████████████] 7/7 (100%)

Comandos: inspect <nombre>, c (continuar), summary, help, exit

👉 Comando: c
```

## 🔧 Configuración Avanzada

### Logging
Para habilitar logging detallado, modifica en `interactive_sim_improved.py`:

```python
logging.basicConfig(
    level=logging.INFO,  # Cambiar a INFO o DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Constantes
Modifica `constants.py` para ajustar valores por defecto:

```python
class CombatConstants:
    MAX_COMBAT_ROUNDS = 100  # Máximo de rondas
    DEFAULT_LEVEL = 5        # Nivel por defecto
    MIN_LEVEL = 1
    MAX_LEVEL = 20
```

## 📝 Notas de Migración

### Desde `interactive_sim.py` Original

1. **Compatibilidad Total**: Los archivos existentes (`configs.py`, `monster_configs.py`, `sim/`) funcionan sin modificaciones

2. **Archivos de Guardado**: Los archivos `.pkl` guardados con la versión anterior son compatibles

3. **Personajes Personalizados**: Los archivos JSON en `custom_chars/` funcionan sin cambios

## 🤝 Contribuciones

### Para Agregar Nueva Funcionalidad

1. **Excepciones**: Agregar a `simulator_exceptions.py`
2. **UI**: Agregar a `ui_utils.py` o `combat_display.py`
3. **Lógica**: Agregar a `combat_manager.py`
4. **Validación**: Agregar a `validation.py`

### Estructura Recomendada

```python
# En validation.py
def validate_new_feature(param):
    """Valida nuevo parámetro"""
    if not is_valid(param):
        raise ValidationException("Error message")
    return param

# En combat_display.py
class CombatDisplay:
    @staticmethod
    def show_new_feature(data):
        """Muestra nueva característica"""
        print(f"{Colors.OKGREEN}{data}{Colors.ENDC}")

# En interactive_sim_improved.py
def new_feature():
    """Nueva funcionalidad"""
    try:
        data = validate_new_feature(get_input())
        CombatDisplay.show_new_feature(data)
    except ValidationException as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
```

## 📚 Recursos

- **Documento de Mejoras**: Ver `MEJORAS_INTERACTIVE_SIM.md` para detalles completos
- **Logs**: Los logs se guardan en memoria (modificar código para persistir)
- **Exportaciones**: Los resultados JSON se guardan en el directorio actual

## 🎯 Roadmap Futuro

### Prioridad Alta
- [ ] Tests unitarios
- [ ] Configuración via archivo YAML/JSON
- [ ] Modo batch para múltiples simulaciones

### Prioridad Media
- [ ] Interfaz gráfica (GUI)
- [ ] Gráficos de resultados
- [ ] Presets de combate

### Prioridad Baja
- [ ] Replay animado de combates
- [ ] Exportación a CSV/Excel
- [ ] Servidor web para acceso remoto

## 🐞 Solución de Problemas

### Error: `ModuleNotFoundError`
```bash
# Verifica que todos los archivos estén en el mismo directorio
ls -la *.py

# Instala dependencias
pip install prettytable
```

### Error: `ImportError: cannot import name 'X'`
```bash
# Verifica que los módulos del proyecto (sim/, configs.py) estén presentes
```

### Los colores no se muestran
- Terminal no compatible con ANSI
- Solución: Usar terminal moderna (Windows Terminal, iTerm2, etc.)

## 📄 Licencia

[Incluir licencia apropiada]

## ✨ Créditos

Desarrollado con mejoras de arquitectura, manejo de errores, y UI mejorada.

---

**¡Que tus dados siempre rueden a tu favor!** 🎲⚔️
