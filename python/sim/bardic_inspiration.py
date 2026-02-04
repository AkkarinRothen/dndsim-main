from util.util import roll_dice

import sim.character
import sim.resource


class BardicInspiration(sim.resource.Resource):
    def __init__(self, character: "sim.character.Character", name: str = "Bardic Inspiration", short_rest: bool = True, die_size: int = 6):
        super().__init__(character, name, short_rest)
        self.die = die_size

    def use(self):
        if super().use(amount=1, detail="Bardic Inspiration"):
            return roll_dice(1, self.die)
        return 0

