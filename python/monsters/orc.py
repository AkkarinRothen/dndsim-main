from sim.monster import BaseMonster

class Orc(BaseMonster):
    def __init__(self):
        super().__init__(
            name="Orc",
            ac=13, # Hide Armor
            hp=15, # 2d8 + 6 = 15 average
            str_score=16, dex=12, con=16, int_score=7, wis=11, cha=10,
            prof_bonus=2, # CR 1/2
            ai_behavior='brute'
        )
