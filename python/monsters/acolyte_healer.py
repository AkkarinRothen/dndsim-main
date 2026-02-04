from sim.monster import BaseMonster
from spells.cure_wounds import CureWounds

class AcolyteHealer(BaseMonster):
    def __init__(self):
        super().__init__(
            name="Acolyte Healer",
            ac=10,
            hp=9, # 2d8 = 9 average
            str_score=10, dex=10, con=10, int_score=10, wis=14, cha=11,
            prof_bonus=2,
            ai_behavior='support',
            caster_level=1,
            spellcasting_ability='wis',
            spells=[CureWounds(level=1)]
        )

    def do_damage(self, target, damage, spell=None, attack=None, multiplier=1.0):
        """A simple do_damage implementation for monsters."""
        import math
        total_damage = math.floor(damage.total() * multiplier)
        target.apply_damage(
            damage=total_damage,
            damage_type=damage.damage_type,
            source=damage.source,
        )
