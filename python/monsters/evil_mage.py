from sim.monster import BaseMonster
from spells.magic_missile import MagicMissile

class EvilMage(BaseMonster):
    def __init__(self):
        super().__init__(
            name="Evil Mage",
            ac=12,
            hp=22, # 5d8 = 22 average
            str_score=9, dex=14, con=11, int_score=17, wis=12, cha=11,
            prof_bonus=2,
            ai_behavior='caster',
            caster_level=3, # 3rd level caster for spell slots
            spellcasting_ability='int',
            spells=[MagicMissile(level=1)]
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
