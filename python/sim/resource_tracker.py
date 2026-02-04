import re
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field

# Import opcional para desarrollo
try:
    import sim.character
except ImportError:
    pass  # El módulo funcionará sin sim.character para ejemplos


@dataclass
class SpellSlotUsage:
    """Rastrea el uso de espacios de conjuro por nivel."""
    level: int
    max_slots: int
    used: int = 0
    spells_cast: List[str] = field(default_factory=list)
    
    def record(self, spell_name: str):
        """Registra el lanzamiento de un conjuro."""
        self.used += 1
        self.spells_cast.append(spell_name)
    
    def remaining(self) -> int:
        """Espacios restantes."""
        return max(0, self.max_slots - self.used)


class CharacterResourceTracker:
    """Rastrea todos los recursos usados por un personaje durante el combate."""
    
    def __init__(self, character: "sim.character.Character"):
        """
        Inicializa el rastreador para un personaje.
        
        Args:
            character: Personaje a rastrear
        """
        self.character = character
        self.name = character.name
        
        # Espacios de conjuro
        self.spell_slots: Dict[int, SpellSlotUsage] = {}
        self._initialize_spell_slots()
        
        # Otras acciones
        self.attacks_made: List[str] = []
        self.bonus_actions: List[str] = []
        self.reactions: List[str] = []
        self.abilities_used: List[str] = []
        
        # Estadísticas de combate
        self.turns_taken = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.hits = 0
        self.misses = 0
        self.crits = 0
    
    def _initialize_spell_slots(self):
        """Inicializa el rastreo de espacios de conjuro."""
        if hasattr(self.character, 'spells') and self.character.spells:
            for level in range(1, 10):  # Niveles 1-9
                max_slots = 0
                if hasattr(self.character.spells, 'slots') and level < len(self.character.spells.slots):
                    max_slots = self.character.spells.slots[level]
                
                if max_slots > 0:
                    self.spell_slots[level] = SpellSlotUsage(
                        level=level,
                        max_slots=max_slots
                    )
    
    def record_spell_cast(self, spell_name: str, level: int):
        """
        Registra el lanzamiento de un conjuro.
        
        Args:
            spell_name: Nombre del conjuro
            level: Nivel del espacio usado
        """
        if level in self.spell_slots:
            self.spell_slots[level].record(spell_name)
    
    def record_attack(self, attack_name: str, hit: bool = True, crit: bool = False):
        """
        Registra un ataque.
        
        Args:
            attack_name: Nombre del ataque
            hit: Si el ataque impactó
            crit: Si fue crítico
        """
        self.attacks_made.append(attack_name)
        if hit:
            self.hits += 1
        else:
            self.misses += 1
        if crit:
            self.crits += 1
    
    def record_damage_dealt(self, damage: int):
        """Registra daño infligido."""
        self.damage_dealt += damage
    
    def record_damage_taken(self, damage: int):
        """Registra daño recibido."""
        self.damage_taken += damage
    
    def record_turn(self):
        """Registra un turno tomado."""
        self.turns_taken += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Genera un resumen completo del uso de recursos.
        
        Returns:
            Diccionario con el resumen completo
        """
        summary = {
            'name': self.name,
            'turns': self.turns_taken,
            'combat_stats': {
                'damage_dealt': self.damage_dealt,
                'damage_taken': self.damage_taken,
                'hits': self.hits,
                'misses': self.misses,
                'crits': self.crits,
                'hit_rate': f"{(self.hits / max(1, self.hits + self.misses) * 100):.1f}%"
            },
            'spell_slots': {},
            'resources': {},
            'round_by_round_usage': defaultdict(lambda: defaultdict(int)),
            'actions': {
                'attacks': self.attacks_made,
                'bonus_actions': self.bonus_actions,
                'reactions': self.reactions,
                'abilities': self.abilities_used
            }
        }
        
        # Espacios de conjuro
        for level, slot_usage in sorted(self.spell_slots.items()):
            if slot_usage.used > 0:
                summary['spell_slots'][f'Level {level}'] = {
                    'used': slot_usage.used,
                    'max': slot_usage.max_slots,
                    'remaining': slot_usage.remaining(),
                    'spells': slot_usage.spells_cast
                }
        
        # Recursos
        if hasattr(self.character, 'resources'):
            for resource in self.character.resources.values():
                resource_summary = resource.get_usage_summary()
                if resource_summary:
                    summary['resources'][resource.name] = resource_summary
                    if resource_summary['details']:
                        for detail in resource_summary['details']:
                            match = re.match(r"Round (\d+): (.*)", detail)
                            if match:
                                round_num, action = match.groups()
                                summary['round_by_round_usage'][int(round_num)][action] += 1

        # Agregando el resumen de resource_usage_summary del personaje
        if hasattr(self.character, 'resource_usage_summary'):
            for category, items in self.character.resource_usage_summary.items():
                if category not in summary['actions']: # Avoid overwriting existing keys
                    summary['actions'][category] = {}
                for item_name, count in items.items():
                    if count > 0:
                        summary['actions'][category][item_name] = count

        return summary
    
    def print_summary(self):
        """Imprime un resumen formateado del uso de recursos."""
        summary = self.get_summary()
        
        print(f"\n{'='*60}")
        print(f"RESUMEN DE RECURSOS: {self.name}")
        print(f"{ '='*60}\n")
        
        # Estadísticas de combate
        stats = summary['combat_stats']
        print(f"📊 ESTADÍSTICAS DE COMBATE")
        print(f"  Turnos:        {summary['turns']}")
        print(f"  Daño infligido: {stats['damage_dealt']}")
        print(f"  Daño recibido:  {stats['damage_taken']}")
        print(f"  Impactos:      {stats['hits']}")
        print(f"  Fallos:        {stats['misses']}")
        print(f"  Críticos:      {stats['crits']}")
        if stats['hits'] + stats['misses'] > 0:
            print(f"  Precisión:     {stats['hit_rate']}")
        
        # Espacios de conjuro
        if summary['spell_slots']:
            print(f"\n✨ ESPACIOS DE CONJURO")
            for name, slot_usage in summary['spell_slots'].items():
                print(f"  {name}: {slot_usage['used']}/{slot_usage['max']} usados "
                      f"({slot_usage['remaining']} restantes)")
                if slot_usage['spells']:
                    for spell in slot_usage['spells']:
                        print(f"    - {spell}")
        
        # Recursos
        if summary['resources']:
            print(f"\n⚡ RECURSOS ESPECIALES")
            for name, usage in summary['resources'].items():
                print(f"  {name}: {usage['used']}/{usage['max']} usados "
                      f"({usage['remaining']} restantes, {usage['percentage']})")
                if usage['details']:
                    for detail in usage['details']:
                        print(f"    - {detail}")

        # Per-round resource usage
        if summary['round_by_round_usage']:
            print(f"\n🔄 USO DE RECURSOS POR RONDA")
            for round_num, actions in sorted(summary['round_by_round_usage'].items()):
                print(f"  Ronda {round_num}:")
                for action, count in actions.items():
                    print(f"    - {action}: {count}x")

        # Consolidar todas las acciones y feats de resource_usage_summary
        all_actions_and_feats = defaultdict(int)
        if hasattr(self.character, 'resource_usage_summary'):
            for category, items in self.character.resource_usage_summary.items():
                for item_name, count in items.items():
                    if count > 0:
                        all_actions_and_feats[item_name] += count
        
        if all_actions_and_feats:
            print(f"\n🚀 ACCIONES Y DOTES USADAS")
            for item_name, count in sorted(all_actions_and_feats.items()):
                print(f"  {item_name}: {count}x")

        print(f"\n{'='*60}\n")


class CombatResourceTracker:
    """Rastrea recursos para todos los personajes en un combate."""
    
    def __init__(self):
        """Inicializa el rastreador de combate."""
        self.trackers: Dict[str, CharacterResourceTracker] = {}
    
    def add_character(self, character: "sim.character.Character"):
        """
        Añade un personaje al rastreo.
        
        Args:
            character: Personaje a rastrear
        """
        tracker = CharacterResourceTracker(character)
        self.trackers[character.name] = tracker
        return tracker
    
    def get_tracker(self, character_name: str) -> Optional[CharacterResourceTracker]:
        """
        Obtiene el rastreador de un personaje.
        
        Args:
            character_name: Nombre del personaje
            
        Returns:
            Rastreador del personaje o None
        """
        return self.trackers.get(character_name)
    
    def print_all_summaries(self):
        """Imprime resúmenes de todos los personajes."""
        print(f"\n{'#'*60}")
        print(f"# RESUMEN FINAL DE COMBATE")
        print(f"{ '#' * 60}")
        
        for tracker in self.trackers.values():
            tracker.print_summary()
    
    def export_summary(self) -> Dict[str, Any]:
        """
        Exporta un resumen completo de todos los personajes.
        
        Returns:
            Diccionario con resúmenes de todos los personajes
        """
        return {
            name: tracker.get_summary()
            for name, tracker in self.trackers.items()
        }


# Función helper para integrar con el sistema existente
def create_tracker_hooks(character: "sim.character.Character", 
                        tracker: CharacterResourceTracker):
    """
    Añade hooks al personaje para rastrear automáticamente el uso de recursos.
    
    Args:
        character: Personaje a modificar
        tracker: Rastreador asociado
    """
    # Rastrear turnos
    original_begin_turn = character.begin_turn
    def tracked_begin_turn(target, **kwargs):
        tracker.record_turn()
        original_begin_turn(target, **kwargs)
    character.begin_turn = tracked_begin_turn
    
    # Rastrear ataques
    original_attack = character.attack
    def tracked_attack(target, attack, **kwargs):
        # El tracking de hit/miss/crit se hace después del ataque
        original_attack(target, attack, **kwargs)
    character.attack = tracked_attack
    
    # Rastrear lanzamiento de conjuros
    if hasattr(character, 'spells') and hasattr(character.spells, 'cast'):
        original_cast = character.spells.cast
        def tracked_cast(spell, *args, **kwargs):
            result = original_cast(spell, *args, **kwargs)
            if hasattr(spell, 'name') and hasattr(spell, 'level'):
                tracker.record_spell_cast(spell.name, spell.level)
            return result
        character.spells.cast = tracked_cast


if __name__ == "__main__":
    # Ejemplo de uso
    print("""
Ejemplo de uso:

# Crear rastreador de combate
combat_tracker = CombatResourceTracker()

# Añadir personajes
tracker1 = combat_tracker.add_character(character1)
tracker2 = combat_tracker.add_character(character2)

# Opcional: Añadir hooks automáticos
create_tracker_hooks(character1, tracker1)
create_tracker_hooks(character2, tracker2)

# Durante el combate, registrar manualmente acciones específicas:
tracker1.record_spell_cast("Fireball", level=3)
# El uso de recursos ahora se rastrea automáticamente a través de la clase Resource
# Ejemplo: character1.resources['Ki'].use(amount=2, detail="Flurry of Blows")

# Al final del combate
combat_tracker.print_all_summaries()

# O exportar como JSON
import json
summary = combat_tracker.export_summary()
print(json.dumps(summary, indent=2))
    """)