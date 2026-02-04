#!/usr/bin/env python3
"""
DEMOSTRACIÓN VISUAL DEL RESOURCE TRACKER
Simula un combate completo y muestra el resumen de recursos
"""

from resource_tracker import CombatResourceTracker
import random


class SimulacionPersonaje:
    """Simulación simplificada de un personaje para demostración."""
    
    def __init__(self, nombre, clase, nivel=10):
        self.name = nombre
        self.clase = clase
        self.nivel = nivel
        
        # Simular recursos según la clase
        class Recurso:
            def __init__(self, max_val):
                self.max = max_val
                self.num = max_val
        
        # Inicializar recursos según clase
        if clase == "Monje":
            self.ki = Recurso(10)
            self.sorcery = Recurso(0)
            self.channel_divinity = Recurso(0)
        elif clase == "Hechicero":
            self.ki = Recurso(0)
            self.sorcery = Recurso(10)
            self.channel_divinity = Recurso(0)
        elif clase == "Clérigo":
            self.ki = Recurso(0)
            self.sorcery = Recurso(0)
            self.channel_divinity = Recurso(3)
        else:  # Guerrero
            self.ki = Recurso(0)
            self.sorcery = Recurso(0)
            self.channel_divinity = Recurso(0)
        
        # Simular espacios de conjuro
        class Spells:
            def max_slots(self, level):
                if clase in ["Hechicero", "Clérigo"]:
                    slots = {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}
                    return slots.get(level, 0)
                return 0
        
        self.spells = Spells()
        
        # Stats de combate
        self.hp = 80
        self.ac = 16


def simular_turno_monje(personaje, tracker, ronda):
    """Simula el turno de un monje."""
    tracker.record_turn()
    
    # Ataque principal
    hit = random.random() > 0.3
    crit = random.random() > 0.9
    tracker.record_attack("Bastón", hit=hit, crit=crit)
    if hit:
        damage = random.randint(8, 12) if not crit else random.randint(16, 24)
        tracker.record_damage_dealt(damage)
    
    # Ataque extra
    hit = random.random() > 0.3
    crit = random.random() > 0.9
    tracker.record_attack("Bastón (Extra Attack)", hit=hit, crit=crit)
    if hit:
        damage = random.randint(8, 12) if not crit else random.randint(16, 24)
        tracker.record_damage_dealt(damage)
    
    # Usar Ki para habilidades
    if ronda % 2 == 0 and personaje.ki.num >= 2:
        personaje.ki.num -= 2
        tracker.record_resource_use("Ki", 2, "Flurry of Blows")
        tracker.bonus_actions.append("Flurry of Blows")
        
        # Dos ataques adicionales
        for i in range(2):
            hit = random.random() > 0.3
            tracker.record_attack(f"Puño desarmado {i+1}", hit=hit, crit=False)
            if hit:
                damage = random.randint(6, 10)
                tracker.record_damage_dealt(damage)
    elif personaje.ki.num >= 1 and random.random() > 0.6:
        personaje.ki.num -= 1
        tracker.record_resource_use("Ki", 1, "Patient Defense")
        tracker.bonus_actions.append("Patient Defense")


def simular_turno_hechicero(personaje, tracker, ronda):
    """Simula el turno de un hechicero."""
    tracker.record_turn()
    
    # Lanzar conjuros
    if ronda == 1:
        # Fireball en la primera ronda
        tracker.record_spell_cast("Fireball", level=3)
        damage = sum(random.randint(1, 6) for _ in range(8))
        tracker.record_damage_dealt(damage)
    elif ronda == 2:
        # Scorching Ray
        tracker.record_spell_cast("Scorching Ray", level=2)
        for i in range(3):
            hit = random.random() > 0.3
            tracker.record_attack(f"Scorching Ray #{i+1}", hit=hit, crit=False)
            if hit:
                damage = sum(random.randint(1, 6) for _ in range(2))
                tracker.record_damage_dealt(damage)
    else:
        # Magic Missile
        tracker.record_spell_cast("Magic Missile", level=1)
        damage = sum(random.randint(1, 4) + 1 for _ in range(3))
        tracker.record_damage_dealt(damage)
    
    # Usar Sorcery Points ocasionalmente
    if random.random() > 0.7 and personaje.sorcery.num >= 2:
        personaje.sorcery.num -= 2
        tracker.record_resource_use("Sorcery", 2, "Quickened Spell")
        tracker.bonus_actions.append("Quickened Spell - Firebolt")
        
        hit = random.random() > 0.3
        tracker.record_attack("Firebolt (Quickened)", hit=hit, crit=False)
        if hit:
            damage = sum(random.randint(1, 10) for _ in range(3))
            tracker.record_damage_dealt(damage)


def simular_turno_clerigo(personaje, tracker, ronda):
    """Simula el turno de un clérigo."""
    tracker.record_turn()
    
    if ronda == 1:
        # Usar Channel Divinity
        if personaje.channel_divinity.num > 0:
            personaje.channel_divinity.num -= 1
            tracker.record_resource_use("Channel Divinity", 1, "Turn Undead")
            tracker.abilities_used.append("Turn Undead")
        
        # Spiritual Weapon
        tracker.record_spell_cast("Spiritual Weapon", level=2)
        tracker.bonus_actions.append("Spiritual Weapon (conjurar)")
    else:
        # Atacar con arma normal
        hit = random.random() > 0.3
        tracker.record_attack("Maza", hit=hit, crit=random.random() > 0.95)
        if hit:
            damage = random.randint(6, 12)
            tracker.record_damage_dealt(damage)
        
        # Atacar con Spiritual Weapon (bonus action)
        hit = random.random() > 0.3
        tracker.record_attack("Spiritual Weapon", hit=hit, crit=False)
        tracker.bonus_actions.append("Spiritual Weapon (ataque)")
        if hit:
            damage = random.randint(6, 12)
            tracker.record_damage_dealt(damage)
    
    # Conjuro de curación ocasional
    if ronda == 3:
        tracker.record_spell_cast("Cure Wounds", level=2)


def simular_turno_guerrero(personaje, tracker, ronda):
    """Simula el turno de un guerrero."""
    tracker.record_turn()
    
    # Ataques normales (4 con Extra Attack mejorado)
    for i in range(4):
        hit = random.random() > 0.25  # Guerreros pegan más
        crit = random.random() > 0.9
        tracker.record_attack(f"Espada larga #{i+1}", hit=hit, crit=crit)
        if hit:
            damage = random.randint(10, 16) if not crit else random.randint(20, 32)
            tracker.record_damage_dealt(damage)
    
    # Action Surge ocasionalmente
    if ronda == 2:
        tracker.abilities_used.append("Action Surge")
        for i in range(4):
            hit = random.random() > 0.25
            crit = random.random() > 0.9
            tracker.record_attack(f"Espada larga (AS) #{i+1}", hit=hit, crit=crit)
            if hit:
                damage = random.randint(10, 16) if not crit else random.randint(20, 32)
                tracker.record_damage_dealt(damage)
    
    # Second Wind
    if ronda == 3:
        tracker.abilities_used.append("Second Wind (15 HP)")
        tracker.bonus_actions.append("Second Wind")


def ejecutar_simulacion():
    """Ejecuta una simulación completa de combate."""
    
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "SIMULACIÓN DE COMBATE D&D 5E" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    
    # Crear personajes
    monje = SimulacionPersonaje("Li Wei", "Monje", 10)
    hechicero = SimulacionPersonaje("Morgana", "Hechicero", 10)
    clerigo = SimulacionPersonaje("Padre Aldric", "Clérigo", 10)
    guerrero = SimulacionPersonaje("Thorin", "Guerrero", 10)
    
    personajes = [monje, hechicero, clerigo, guerrero]
    
    # Crear tracker
    combat_tracker = CombatResourceTracker()
    trackers = {
        "Li Wei": combat_tracker.add_character(monje),
        "Morgana": combat_tracker.add_character(hechicero),
        "Padre Aldric": combat_tracker.add_character(clerigo),
        "Thorin": combat_tracker.add_character(guerrero),
    }
    
    # Simular 5 rondas de combate
    print("\n🎲 Simulando 5 rondas de combate...\n")
    
    for ronda in range(1, 6):
        print(f"{'─'*70}")
        print(f"🗡️  RONDA {ronda}")
        print(f"{'─'*70}")
        
        # Turno del monje
        print("  ▸ Li Wei (Monje) toma su turno...")
        simular_turno_monje(monje, trackers["Li Wei"], ronda)
        
        # Turno del hechicero
        print("  ▸ Morgana (Hechicero) toma su turno...")
        simular_turno_hechicero(hechicero, trackers["Morgana"], ronda)
        
        # Turno del clérigo
        print("  ▸ Padre Aldric (Clérigo) toma su turno...")
        simular_turno_clerigo(clerigo, trackers["Padre Aldric"], ronda)
        
        # Turno del guerrero
        print("  ▸ Thorin (Guerrero) toma su turno...")
        simular_turno_guerrero(guerrero, trackers["Thorin"], ronda)
        
        print()
    
    print("╔" + "="*68 + "╗")
    print("║" + " "*22 + "COMBATE FINALIZADO" + " "*28 + "║")
    print("╚" + "="*68 + "╝")
    
    # Mostrar resúmenes
    combat_tracker.print_all_summaries()
    
    # Exportar a JSON
    import json
    summary = combat_tracker.export_summary()
    
    filename = '/mnt/user-data/outputs/simulacion_combate.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print(f"✅ Resumen completo exportado a: {filename}")
    print("="*70)
    
    # Mostrar análisis rápido
    print("\n╔" + "="*68 + "╗")
    print("║" + " "*25 + "ANÁLISIS RÁPIDO" + " "*28 + "║")
    print("╚" + "="*68 + "╝\n")
    
    for nombre, datos in summary.items():
        stats = datos['combat_stats']
        dpt = stats['damage_dealt'] / datos['turns'] if datos['turns'] > 0 else 0
        print(f"🎯 {nombre}:")
        print(f"   ├─ Daño total: {stats['damage_dealt']}")
        print(f"   ├─ DPT (Daño Por Turno): {dpt:.1f}")
        print(f"   ├─ Precisión: {stats['hit_rate']}")
        print(f"   └─ Críticos: {stats['crits']}")
        print()


if __name__ == "__main__":
    ejecutar_simulacion()
