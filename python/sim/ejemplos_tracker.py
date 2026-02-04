"""
Ejemplo de integración del sistema de rastreo de recursos.

Este script muestra cómo usar el ResourceTracker con tus clases Character y Resource
existentes para obtener un resumen detallado del uso de recursos al final del combate.
"""

# Importaciones necesarias (ajusta según tu estructura de proyecto)
# from sim.character import Character
# from sim.resource import Resource
# from sim.target import Target
from resource_tracker import (
    CombatResourceTracker,
    CharacterResourceTracker,
    create_tracker_hooks
)


def ejemplo_simple():
    """Ejemplo básico de uso manual del tracker."""
    print("="*70)
    print("EJEMPLO 1: USO MANUAL DEL TRACKER")
    print("="*70)
    
    # Nota: Este es un ejemplo conceptual
    # En tu código real, reemplazarías esto con tus objetos Character reales
    
    class MockCharacter:
        def __init__(self, name):
            self.name = name
            
            # Simular recursos
            class MockResource:
                def __init__(self, max_val):
                    self.max = max_val
                    self.num = max_val
            
            self.ki = MockResource(5)
            self.sorcery = MockResource(0)
            self.channel_divinity = MockResource(2)
            
            # Simular spells
            class MockSpells:
                def max_slots(self, level):
                    slots = {1: 4, 2: 3, 3: 3, 4: 2, 5: 1}
                    return slots.get(level, 0)
            
            self.spells = MockSpells()
    
    # Crear personajes mock
    fighter = MockCharacter("Gorak el Guerrero")
    wizard = MockCharacter("Elara la Maga")
    
    # Crear rastreador de combate
    combat_tracker = CombatResourceTracker()
    
    # Añadir personajes al rastreador
    fighter_tracker = combat_tracker.add_character(fighter)
    wizard_tracker = combat_tracker.add_character(wizard)
    
    # Simular combate - Turno 1 del Fighter
    print("\n[Turno 1 - Gorak]")
    fighter_tracker.record_turn()
    fighter_tracker.record_attack("Espada larga", hit=True, crit=False)
    fighter_tracker.record_damage_dealt(12)
    fighter_tracker.record_attack("Ataque extra", hit=True, crit=False)
    fighter_tracker.record_damage_dealt(10)
    fighter_tracker.record_resource_use("Ki", amount=1, detail="Patient Defense")
    
    # Simular combate - Turno 1 del Wizard
    print("[Turno 1 - Elara]")
    wizard_tracker.record_turn()
    wizard_tracker.record_spell_cast("Magic Missile", level=1)
    wizard_tracker.record_damage_dealt(10)
    
    # Turno 2 del Fighter
    print("\n[Turno 2 - Gorak]")
    fighter_tracker.record_turn()
    fighter_tracker.record_attack("Espada larga", hit=False, crit=False)
    fighter_tracker.record_attack("Ataque extra", hit=True, crit=True)
    fighter_tracker.record_damage_dealt(22)
    fighter_tracker.record_resource_use("Ki", amount=2, detail="Flurry of Blows")
    fighter_tracker.bonus_actions.append("Flurry of Blows (2 ataques)")
    
    # Turno 2 del Wizard
    print("[Turno 2 - Elara]")
    wizard_tracker.record_turn()
    wizard_tracker.record_spell_cast("Fireball", level=3)
    wizard_tracker.record_damage_dealt(28)
    
    # Turno 3 del Fighter
    print("\n[Turno 3 - Gorak]")
    fighter_tracker.record_turn()
    fighter_tracker.record_attack("Espada larga", hit=True, crit=False)
    fighter_tracker.record_damage_dealt(11)
    fighter_tracker.record_attack("Ataque extra", hit=True, crit=False)
    fighter_tracker.record_damage_dealt(9)
    fighter_tracker.record_resource_use("Channel Divinity", amount=1, 
                                       detail="Sacred Weapon")
    
    # Turno 3 del Wizard
    print("[Turno 3 - Elara]")
    wizard_tracker.record_turn()
    wizard_tracker.record_spell_cast("Shield", level=1)
    wizard_tracker.reactions.append("Shield (vs ataque)")
    wizard_tracker.record_spell_cast("Scorching Ray", level=2)
    wizard_tracker.record_damage_dealt(15)
    
    # Mostrar resúmenes
    combat_tracker.print_all_summaries()


def ejemplo_con_hooks():
    """Ejemplo usando hooks automáticos."""
    print("\n" + "="*70)
    print("EJEMPLO 2: USO CON HOOKS AUTOMÁTICOS")
    print("="*70)
    print("""
Si usas create_tracker_hooks(), el tracking se hace automáticamente:

# Crear rastreador
combat_tracker = CombatResourceTracker()
tracker = combat_tracker.add_character(character)

# Instalar hooks automáticos
create_tracker_hooks(character, tracker)

# Ahora cuando el personaje haga acciones, se registran automáticamente:
character.begin_turn(target)  # → tracker.record_turn() se llama automáticamente
character.ki.use(2)           # → tracker.record_resource_use('Ki', 2) automático
character.spells.cast(spell)  # → tracker.record_spell_cast() automático

# Al final del combate:
combat_tracker.print_all_summaries()
    """)


def ejemplo_exportar_json():
    """Ejemplo de cómo exportar los datos a JSON."""
    print("\n" + "="*70)
    print("EJEMPLO 3: EXPORTAR A JSON")
    print("="*70)
    
    import json
    
    # Crear un tracker simple con datos de ejemplo
    class MockChar:
        def __init__(self, name):
            self.name = name
            class R:
                max = 0
            self.ki = R()
            self.sorcery = R()
            self.channel_divinity = R()
            class S:
                def max_slots(self, l):
                    return 0
            self.spells = S()
    
    combat_tracker = CombatResourceTracker()
    char = MockChar("Ejemplo")
    tracker = combat_tracker.add_character(char)
    
    # Añadir algunos datos
    tracker.record_turn()
    tracker.record_attack("Espada", hit=True, crit=False)
    tracker.record_damage_dealt(15)
    
    # Exportar a JSON
    summary = combat_tracker.export_summary()
    json_output = json.dumps(summary, indent=2, ensure_ascii=False)
    
    print("\nJSON exportado:")
    print(json_output)
    
    print("\nEste JSON puede ser:")
    print("  • Guardado en un archivo")
    print("  • Enviado a una API")
    print("  • Procesado por otras herramientas")
    print("  • Usado para análisis estadístico")


def integracion_completa_ejemplo():
    """Ejemplo de integración completa en un loop de combate."""
    print("\n" + "="*70)
    print("EJEMPLO 4: INTEGRACIÓN EN LOOP DE COMBATE")
    print("="*70)
    
    codigo_ejemplo = '''
# ============================================
# INTEGRACIÓN EN TU CÓDIGO DE COMBATE EXISTENTE
# ============================================

from resource_tracker import CombatResourceTracker, create_tracker_hooks

def ejecutar_combate(characters, target, num_rounds=10):
    """
    Ejecuta un combate con tracking completo de recursos.
    
    Args:
        characters: Lista de objetos Character
        target: Objetivo del combate
        num_rounds: Número de rondas a simular
    """
    # 1. Crear el rastreador de combate
    combat_tracker = CombatResourceTracker()
    
    # 2. Añadir todos los personajes y configurar hooks
    trackers = {}
    for char in characters:
        tracker = combat_tracker.add_character(char)
        create_tracker_hooks(char, tracker)
        trackers[char.name] = tracker
    
    # 3. Ejecutar el combate (tu lógica existente)
    for round_num in range(num_rounds):
        print(f"\\n=== RONDA {round_num + 1} ===")
        
        for char in characters:
            # Tu lógica de combate existente
            char.turn(target)
            
            # Tracking manual adicional si es necesario
            tracker = trackers[char.name]
            
            # Ejemplo: si detectas una reacción
            # tracker.reactions.append("Opportunity Attack")
            
            # Ejemplo: si detectas una acción bonus específica
            # tracker.bonus_actions.append("Second Wind")
            
            if target.hp <= 0:
                print(f"\\n¡{target.name} ha sido derrotado!")
                break
        
        if target.hp <= 0:
            break
    
    # 4. Mostrar resumen final
    print("\\n" + "="*70)
    print("COMBATE TERMINADO - GENERANDO RESUMEN DE RECURSOS")
    print("="*70)
    
    combat_tracker.print_all_summaries()
    
    # 5. Opcional: Exportar a archivo
    import json
    summary = combat_tracker.export_summary()
    with open('combate_resumen.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("\\n✅ Resumen guardado en 'combate_resumen.json'")
    
    return combat_tracker


# USO:
# tracker = ejecutar_combate([personaje1, personaje2], enemigo, num_rounds=10)
'''
    print(codigo_ejemplo)


def ejemplo_tracking_manual_detallado():
    """Ejemplo mostrando cómo hacer tracking manual detallado."""
    print("\n" + "="*70)
    print("EJEMPLO 5: TRACKING MANUAL DETALLADO")
    print("="*70)
    
    ejemplo = '''
# Si prefieres control total, puedes hacer tracking manual:

tracker = CharacterResourceTracker(character)

# Rastrear un turno completo
tracker.record_turn()

# Rastrear ataques con detalles
tracker.record_attack("Espada larga", hit=True, crit=False)
tracker.record_damage_dealt(12)

tracker.record_attack("Espada larga (Extra Attack)", hit=True, crit=True)
tracker.record_damage_dealt(24)

# Rastrear uso de recursos con contexto
tracker.record_resource_use("Ki", amount=1, detail="Step of the Wind")

# Rastrear conjuros
tracker.record_spell_cast("Cure Wounds", level=2)

# Rastrear acciones bonus específicas
tracker.bonus_actions.append("Flurry of Blows")

# Rastrear reacciones
tracker.reactions.append("Shield")

# Rastrear habilidades especiales
tracker.abilities_used.append("Action Surge")
tracker.abilities_used.append("Second Wind")

# Rastrear daño recibido
tracker.record_damage_taken(15)

# Al final, imprimir resumen
tracker.print_summary()
'''
    print(ejemplo)


def ejemplo_analisis_post_combate():
    """Ejemplo de análisis post-combate."""
    print("\n" + "="*70)
    print("EJEMPLO 6: ANÁLISIS POST-COMBATE")
    print("="*70)
    
    ejemplo = '''
# Después del combate, puedes analizar el uso de recursos:

summary = combat_tracker.export_summary()

for char_name, char_data in summary.items():
    print(f"\\n{char_name}:")
    
    # Analizar eficiencia de ataques
    stats = char_data['combat_stats']
    print(f"  Precisión: {stats['hit_rate']}")
    print(f"  Daño promedio por turno: {stats['damage_dealt'] / char_data['turns']:.1f}")
    
    # Analizar uso de recursos mágicos
    if char_data['spell_slots']:
        total_slots_used = sum(s['used'] for s in char_data['spell_slots'].values())
        print(f"  Total espacios de conjuro usados: {total_slots_used}")
        
        # Conjuros más usados
        all_spells = []
        for slot_data in char_data['spell_slots'].values():
            all_spells.extend(slot_data['spells'])
        
        from collections import Counter
        spell_counts = Counter(all_spells)
        print(f"  Conjuro más usado: {spell_counts.most_common(1)}")
    
    # Analizar eficiencia de recursos
    if char_data['resources']:
        for resource_name, resource_data in char_data['resources'].items():
            efficiency = (resource_data['used'] / resource_data['max']) * 100
            print(f"  {resource_name}: {efficiency:.0f}% utilizado")
    
    # Acciones por turno
    actions_per_turn = len(char_data['actions']['attacks']) / char_data['turns']
    print(f"  Promedio de ataques por turno: {actions_per_turn:.1f}")
'''
    print(ejemplo)


if __name__ == "__main__":
    # Ejecutar todos los ejemplos
    ejemplo_simple()
    ejemplo_con_hooks()
    ejemplo_exportar_json()
    integracion_completa_ejemplo()
    ejemplo_tracking_manual_detallado()
    ejemplo_analisis_post_combate()
    
    print("\n" + "="*70)
    print("RESUMEN DE CARACTERÍSTICAS")
    print("="*70)
    print("""
El sistema de Resource Tracker te permite:

✅ Rastrear automáticamente:
   • Espacios de conjuro usados por nivel
   • Recursos especiales (Ki, Sorcery Points, Channel Divinity, etc.)
   • Ataques realizados (con hit/miss/crit)
   • Daño infligido y recibido
   • Acciones bonus y reacciones
   • Habilidades especiales usadas

✅ Generar reportes detallados:
   • Resumen por personaje
   • Estadísticas de combate
   • Lista de conjuros lanzados
   • Recursos restantes
   • Precisión de ataques

✅ Exportar datos:
   • Formato JSON para análisis
   • Guardar en archivos
   • Integración con otras herramientas

✅ Dos modos de uso:
   1. Automático: con create_tracker_hooks()
   2. Manual: llamando métodos del tracker directamente

¡Perfecto para analizar el rendimiento y optimizar estrategias!
    """)
