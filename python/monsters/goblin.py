from sim.monster import BaseMonster

class Goblin(BaseMonster):
    def __init__(self):
        super().__init__(
            name="Goblin",
            ac=15, # Leather Armor (11) + Dex Mod (2) + Shield (2)
            hp=7,  # 2d6 = 7 average
            str_score=8, dex=14, con=10, int_score=10, wis=8, cha=8,
            prof_bonus=2 # CR 1/4
        )
