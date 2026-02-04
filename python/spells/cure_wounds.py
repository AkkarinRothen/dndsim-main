import random
from sim.spells import Spell, School

class CureWounds(Spell):
    """
    Cure Wounds spell implementation. Heals a creature you touch.
    """
    def __init__(self, level: int = 1):
        """
        Initializes a Cure Wounds spell.
        
        Args:
            level: The spell slot level used to cast the spell.
        """
        super().__init__(
            name="Cure Wounds",
            slot=level,
            school=School.EVOCATION
        )
        self.level = level

    def cast(self, character, target) -> None:
        """
        Casts Cure Wounds, healing the target.
        """
        if not target:
            return
            
        super().cast(character, target)
        
        healing = 0
        for _ in range(self.level):
            healing += random.randint(1, 8)
        
        healing += character.mod(character.spells.mod)
        
        target.hp = min(target.max_hp, target.hp + healing)
        # We need a way to log this, which will be handled via the combat log
        # in the monster's turn method.
