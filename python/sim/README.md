# Sistema de Rastreo de Recursos para D&D 5e

Sistema completo para rastrear el uso de habilidades, conjuros y recursos durante combates de D&D 5e.

## 🎯 Características

- ✨ Rastreo automático de espacios de conjuro por nivel
- ⚡ Monitoreo de recursos especiales (Ki, Sorcery Points, Channel Divinity, etc.)
- ⚔️  Seguimiento de ataques, daño, impactos y críticos
- 📊 Estadísticas detalladas de combate
- 📁 Exportación a JSON para análisis
- 🔄 Integración fácil con código existente

## 🚀 Instalación Rápida

1. Copia `resource_tracker.py` a tu directorio de proyecto
2. Importa las clases necesarias:

```python
from resource_tracker import CombatResourceTracker, create_tracker_hooks
```

## 📖 Uso Básico

### Opción 1: Tracking Automático (Recomendado)

```python
# 1. Crear rastreador de combate
combat_tracker = CombatResourceTracker()

# 2. Añadir personajes
tracker1 = combat_tracker.add_character(personaje1)
tracker2 = combat_tracker.add_character(personaje2)

# 3. Instalar hooks automáticos
create_tracker_hooks(personaje1, tracker1)
create_tracker_hooks(personaje2, tracker2)

# 4. Ejecutar combate normalmente
for round in range(10):
    personaje1.turn(target)
    personaje2.turn(target)

# 5. Ver resumen al final
combat_tracker.print_all_summaries()
```

### Opción 2: Tracking Manual

```python
tracker = CharacterResourceTracker(personaje)

# Durante el combate
tracker.record_turn()
tracker.record_attack("Espada larga", hit=True, crit=False)
tracker.record_damage_dealt(12)
tracker.record_spell_cast("Fireball", level=3)
tracker.record_resource_use("Ki", amount=2, detail="Flurry of Blows")

# Al final
tracker.print_summary()
```

## 📊 Ejemplo de Salida

```
============================================================
RESUMEN DE RECURSOS: Gorak el Guerrero
============================================================

📊 ESTADÍSTICAS DE COMBATE
  Turnos:        3
  Daño infligido: 64
  Daño recibido:  15
  Impactos:      5
  Fallos:        1
  Críticos:      1
  Precisión:     83.3%

⚡ RECURSOS ESPECIALES
  Ki Points: 3/5 usados (2 restantes, 60%)
    - Patient Defense
    - Flurry of Blows
  Channel Divinity: 1/2 usados (1 restantes, 50%)
    - Sacred Weapon

⚔️  ATAQUES REALIZADOS (6)
  Espada larga: 3x
  Ataque extra: 3x

🎯 ACCIONES BONUS (1)
  - Flurry of Blows (2 ataques)

============================================================
```

## 🔧 Integración Completa

```python
def ejecutar_combate(characters, target, num_rounds=10):
    """Combate con tracking completo."""
    # Configurar tracking
    combat_tracker = CombatResourceTracker()
    trackers = {}
    
    for char in characters:
        tracker = combat_tracker.add_character(char)
        create_tracker_hooks(char, tracker)
        trackers[char.name] = tracker
    
    # Ejecutar combate
    for round_num in range(num_rounds):
        for char in characters:
            char.turn(target)
            if target.hp <= 0:
                break
        if target.hp <= 0:
            break
    
    # Mostrar resumen
    combat_tracker.print_all_summaries()
    
    # Exportar a JSON
    import json
    summary = combat_tracker.export_summary()
    with open('resumen_combate.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return combat_tracker
```

## 📝 Métodos Disponibles

### CharacterResourceTracker

| Método | Descripción |
|--------|-------------|
| `record_turn()` | Registra que el personaje tomó un turno |
| `record_attack(name, hit, crit)` | Registra un ataque |
| `record_spell_cast(name, level)` | Registra el lanzamiento de un conjuro |
| `record_resource_use(name, amount, detail)` | Registra uso de recurso |
| `record_damage_dealt(damage)` | Registra daño infligido |
| `record_damage_taken(damage)` | Registra daño recibido |
| `print_summary()` | Imprime resumen formateado |
| `get_summary()` | Retorna diccionario con el resumen |

### CombatResourceTracker

| Método | Descripción |
|--------|-------------|
| `add_character(character)` | Añade un personaje al tracking |
| `get_tracker(name)` | Obtiene el tracker de un personaje |
| `print_all_summaries()` | Imprime resúmenes de todos |
| `export_summary()` | Exporta todo a diccionario |

## 🎯 Casos de Uso

### 1. Análisis de Eficiencia

```python
summary = tracker.get_summary()
hit_rate = summary['combat_stats']['hit_rate']
avg_damage = summary['combat_stats']['damage_dealt'] / summary['turns']
print(f"Precisión: {hit_rate}, Daño promedio/turno: {avg_damage:.1f}")
```

### 2. Optimización de Recursos

```python
for resource_name, data in summary['resources'].items():
    if data['percentage'] < 50:
        print(f"⚠️  {resource_name} infrautilizado: {data['percentage']}")
```

### 3. Comparación de Personajes

```python
combat_tracker.print_all_summaries()
summary = combat_tracker.export_summary()

for name, data in summary.items():
    dps = data['combat_stats']['damage_dealt'] / data['turns']
    print(f"{name}: {dps:.1f} DPT")
```

## 🔍 Datos Rastreados

### Automáticamente
- ✅ Espacios de conjuro (niveles 1-9)
- ✅ Ki Points
- ✅ Sorcery Points
- ✅ Channel Divinity
- ✅ Bardic Inspiration
- ✅ Recursos personalizados (character.resources)

### Manualmente (opcionales)
- 🎯 Acciones bonus específicas
- 🛡️  Reacciones
- 🌟 Habilidades especiales
- 📍 Contexto detallado de uso de recursos

## 🐛 Debugging

Si no ves algunos recursos rastreados:

1. Verifica que el personaje tenga el recurso:
   ```python
   print(f"Ki max: {character.ki.max}")
   print(f"Sorcery max: {character.sorcery.max}")
   ```

2. Verifica que los hooks estén instalados:
   ```python
   create_tracker_hooks(character, tracker)
   ```

3. Para tracking manual, llama los métodos explícitamente:
   ```python
   tracker.record_resource_use("Ki", 1, "Flurry of Blows")
   ```

## 💡 Tips y Trucos

### Tip 1: Agregar Recursos Personalizados
```python
# Si tienes un recurso custom
custom_resource = Resource(character, "Rage", short_rest=False)
custom_resource.increase_max(3)

# El tracker lo detectará automáticamente si está en:
character.resources['Rage'] = custom_resource
```

### Tip 2: Tracking de Eventos Específicos
```python
# Puedes añadir detalles manualmente
tracker.abilities_used.append("Action Surge")
tracker.bonus_actions.append("Second Wind (11 HP)")
tracker.reactions.append("Counterspell (vs Fireball)")
```

### Tip 3: Análisis Post-Combate
```python
# Guardar para análisis posterior
import json
import datetime

summary = combat_tracker.export_summary()
summary['metadata'] = {
    'date': str(datetime.datetime.now()),
    'scenario': 'Dragon Fight',
    'party_level': 10
}

with open(f'combate_{datetime.date.today()}.json', 'w') as f:
    json.dump(summary, f, indent=2)
```

## 🤝 Contribuciones

Si encuentras bugs o tienes sugerencias:
1. Revisa los ejemplos en `ejemplos_tracker.py`
2. Consulta este README
3. Modifica el código según tus necesidades

## 📄 Licencia

Este código es de uso libre. Úsalo, modifícalo y distribúyelo como desees.

## 🎮 ¡Disfruta rastreando tus combates!

¿Preguntas? Revisa los ejemplos en `ejemplos_tracker.py` para ver más casos de uso.
