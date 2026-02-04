import random
from sim.spells import Spell, School
import sim.attack

class MagicMissile(Spell):
    """
    Magic Missile spell implementation.
    Creates one or more darts of magical force that automatically hit a target.
    """
    def __init__(self, level: int = 1):
        """
        Initializes a Magic Missile spell.
        
        Args:
            level: The spell slot level used to cast the spell.
        """
        # For each spell slot level above 1st, an additional dart is created.
        num_darts = 3 + (level - 1)
        
        super().__init__(
            name="Magic Missile",
            slot=level,
            school=School.EVOCATION,
            damage_type="force"
        )
        self.num_darts = num_darts

    def cast(self, character, target) -> None:
        """
        Casts Magic Missile, dealing damage to the target.
        """
        if not target:
            return
            
        super().cast(character, target)
        
        total_damage = 0
        for _ in range(self.num_darts):
            # Each dart deals 1d4+1 force damage
            damage = random.randint(1, 4) + 1
            total_damage += damage
            
        damage_roll = sim.attack.DamageRoll(
            source=self.name,
            damage_type=self.damage_type,
            flat_dmg=total_damage
        )
        
        # In the context of a monster casting, the 'character' is the monster itself.
        # We need a way for the monster to call 'do_damage'.
        # For now, let's assume the monster has a 'do_damage' method like a character.
        # This is a simplification and might need to be adjusted.
        if hasattr(character, 'do_damage'):
             character.do_damage(target, damage_roll, spell=self)
        else:
            # Fallback for entities that don't have do_damage
            target.apply_damage(total_damage, self.damage_type, self.name)

