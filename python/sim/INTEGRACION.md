"""
GUÍA DE INTEGRACIÓN ESPECÍFICA
Para tus archivos character.py y resource.py

Este archivo muestra exactamente cómo integrar el ResourceTracker
con tu código existente.
"""

# ============================================================================
# PASO 1: Importar el sistema de tracking
# ============================================================================

from resource_tracker import CombatResourceTracker, CharacterResourceTracker


# ============================================================================
# PASO 2: Modificar tu loop de combate principal
# ============================================================================

def ejecutar_combate_con_tracking(personajes, objetivo, num_rondas=10):
    """
    Función ejemplo de cómo integrar el tracking en tu combate.
    
    Args:
        personajes: Lista de objetos Character (de tu character.py)
        objetivo: Objetivo del combate (Target)
        num_rondas: Número de rondas a simular
    """
    
    # 1. Crear el rastreador de combate
    combat_tracker = CombatResourceTracker()
    trackers = {}
    
    # 2. Añadir cada personaje al tracking
    for personaje in personajes:
        tracker = combat_tracker.add_character(personaje)
        trackers[personaje.name] = tracker
    
    # 3. Ejecutar el combate
    print("="*70)
    print("INICIANDO COMBATE")
    print("="*70)
    
    for ronda in range(num_rondas):
        print(f"\n--- RONDA {ronda + 1} ---")
        
        for personaje in personajes:
            print(f"\nTurno de {personaje.name}")
            
            # Tracking del turno
            tracker = trackers[personaje.name]
            tracker.record_turn()
            
            # Ejecutar el turno del personaje (tu código existente)
            personaje.turn(objetivo)
            
            # IMPORTANTE: Aquí necesitas agregar tracking manual para eventos
            # que no se detectan automáticamente. Por ejemplo:
            
            # Si usaste Ki Points (detecta el uso en el método):
            # El tracking de Ki se puede hacer automáticamente si modificas
            # el método use() de Resource
            
            # Si verificas el objetivo
            if objetivo.hp <= 0:
                print(f"\n¡{objetivo.name} ha sido derrotado!")
                break
        
        if objetivo.hp <= 0:
            break
    
    # 4. Mostrar resumen final
    print("\n" + "="*70)
    print("COMBATE FINALIZADO - RESUMEN DE RECURSOS")
    print("="*70)
    
    combat_tracker.print_all_summaries()
    
    # 5. Exportar a JSON (opcional)
    import json
    summary = combat_tracker.export_summary()
    
    filename = 'resumen_combate.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Resumen exportado a '{filename}'")
    
    return combat_tracker, summary


# ============================================================================
# PASO 3: Modificar la clase Resource para tracking automático
# ============================================================================

"""
Para rastrear automáticamente el uso de recursos, puedes modificar
tu archivo resource.py de esta manera:

# En resource.py, añade al principio:

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from resource_tracker import CharacterResourceTracker

# Luego, en la clase Resource, modifica __init__:

class Resource(sim.event_loop.Listener):
    def __init__(
        self,
        character: "sim.character.Character",
        name: str,
        short_rest: bool = False,
        tracker: Optional["CharacterResourceTracker"] = None  # NUEVO
    ):
        self.name = name
        self.num = 0
        self.max = 0
        self.reset_on_short_rest = short_rest
        self.tracker = tracker  # NUEVO
        
        character.events.add(self, ["short_rest", "long_rest"])

# Y modifica el método use():

    def use(self, amount: int = 1) -> bool:
        if amount < 0:
            raise ValueError(f"Cannot use negative amount: {amount}")
        
        if self.num >= amount:
            log.record(f"Resource ({self.name})", amount)
            self.num -= amount
            
            # NUEVO: Tracking automático
            if self.tracker:
                self.tracker.record_resource_use(
                    self.name, 
                    amount,
                    detail=None  # Puedes añadir contexto si quieres
                )
            
            return True
        
        return False
"""


# ============================================================================
# PASO 4: Tracking manual detallado (alternativa más simple)
# ============================================================================

def ejecutar_combate_tracking_manual(personajes, objetivo, num_rondas=10):
    """
    Versión con tracking completamente manual.
    No requiere modificar tus archivos existentes.
    """
    
    # Crear trackers
    combat_tracker = CombatResourceTracker()
    trackers = {p.name: combat_tracker.add_character(p) for p in personajes}
    
    for ronda in range(num_rondas):
        for personaje in personajes:
            tracker = trackers[personaje.name]
            
            # Registrar estado antes del turno
            ki_antes = personaje.ki.num
            sorcery_antes = personaje.sorcery.num
            channel_antes = personaje.channel_divinity.num
            
            # Espacios de conjuro antes
            slots_antes = {}
            for nivel in range(1, 10):
                if hasattr(personaje.spells, 'slots'):
                    slots_antes[nivel] = personaje.spells.slots.get(nivel, 0)
            
            # Ejecutar turno
            tracker.record_turn()
            personaje.turn(objetivo)
            
            # Detectar qué recursos se usaron
            ki_usado = ki_antes - personaje.ki.num
            if ki_usado > 0:
                tracker.record_resource_use("Ki", ki_usado)
            
            sorcery_usado = sorcery_antes - personaje.sorcery.num
            if sorcery_usado > 0:
                tracker.record_resource_use("Sorcery", sorcery_usado)
            
            channel_usado = channel_antes - personaje.channel_divinity.num
            if channel_usado > 0:
                tracker.record_resource_use("Channel Divinity", channel_usado)
            
            # Detectar conjuros lanzados
            for nivel in range(1, 10):
                if hasattr(personaje.spells, 'slots'):
                    slots_ahora = personaje.spells.slots.get(nivel, 0)
                    slots_usados = slots_antes.get(nivel, 0) - slots_ahora
                    if slots_usados > 0:
                        # No sabemos el nombre exacto del conjuro sin más info,
                        # pero podemos registrar que se usó un slot
                        tracker.record_spell_cast(f"Spell (Level {nivel})", nivel)
            
            if objetivo.hp <= 0:
                break
        
        if objetivo.hp <= 0:
            break
    
    # Mostrar resumen
    combat_tracker.print_all_summaries()
    return combat_tracker


# ============================================================================
# PASO 5: Integración con el sistema de eventos
# ============================================================================

"""
Otra opción es usar el sistema de eventos que ya tienes en character.py.
Puedes crear un Listener que registre automáticamente las acciones:

from sim.event_loop import Listener

class ResourceTrackerListener(Listener):
    def __init__(self, character, tracker):
        self.character = character
        self.tracker = tracker
        
        # Suscribirse a eventos relevantes
        character.events.add(self, [
            "begin_turn",
            "attack_result", 
            "damage_roll",
            # Añade más eventos según necesites
        ])
    
    def begin_turn(self, target):
        self.tracker.record_turn()
    
    def attack_result(self, result):
        # result es un AttackResultArgs
        attack_name = result.attack.attack.name
        self.tracker.record_attack(
            attack_name,
            hit=result.hit,
            crit=result.crit
        )
    
    def damage_roll(self, args):
        # args es un DamageRollArgs
        # Registrar daño (esto requiere más lógica para saber
        # si es daño infligido o recibido)
        pass

# Uso:
tracker = combat_tracker.add_character(personaje)
listener = ResourceTrackerListener(personaje, tracker)
"""


# ============================================================================
# EJEMPLO COMPLETO DE USO
# ============================================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  GUÍA DE INTEGRACIÓN DEL RESOURCE TRACKER                          ║
║  Con tus archivos character.py y resource.py                       ║
╚════════════════════════════════════════════════════════════════════╝

Tienes 3 opciones principales:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPCIÓN 1: Tracking Manual Completo (MÁS SIMPLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ No requiere modificar tus archivos existentes
✅ Control total sobre qué se registra
✅ Fácil de implementar

Usa la función: ejecutar_combate_tracking_manual()


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPCIÓN 2: Modificar Resource.use() (SEMI-AUTOMÁTICO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Tracking automático de Ki, Sorcery, Channel Divinity
✅ Requiere pequeña modificación en resource.py
✅ Más elegante que tracking manual

Ver comentarios en "PASO 3" arriba


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPCIÓN 3: Sistema de Eventos (MÁS AVANZADO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Totalmente automático
✅ Usa el sistema de eventos que ya tienes
✅ Requiere crear un Listener personalizado

Ver comentarios en "PASO 5" arriba


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMENDACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Si quieres algo rápido y funcional:
→ Usa OPCIÓN 1 (tracking manual)

Si quieres algo más integrado:
→ Usa OPCIÓN 2 (modificar resource.py)

Si quieres la solución más elegante:
→ Usa OPCIÓN 3 (sistema de eventos)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EJEMPLO MÍNIMO DE CÓDIGO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from resource_tracker import CombatResourceTracker

# Crear tracker
combat_tracker = CombatResourceTracker()

# Añadir personajes
tracker1 = combat_tracker.add_character(personaje1)
tracker2 = combat_tracker.add_character(personaje2)

# Tu loop de combate normal...
for ronda in range(10):
    # Antes del turno
    tracker1.record_turn()
    ki_antes = personaje1.ki.num
    
    # Ejecutar turno
    personaje1.turn(objetivo)
    
    # Después del turno - detectar uso
    ki_usado = ki_antes - personaje1.ki.num
    if ki_usado > 0:
        tracker1.record_resource_use("Ki", ki_usado)

# Al final
combat_tracker.print_all_summaries()


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¡Espero que esto te ayude a rastrear los recursos en tus combates! 🎲⚔️
    """)
