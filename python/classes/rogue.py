import math
from typing import List, Optional

from util.util import (
    apply_asi_feats,
    get_magic_weapon,
    do_roll,
)
from feats.epic_boons import IrresistibleOffense
from feats import ASI, AttackAction, WeaponMasteries
from weapons import Shortsword, Scimitar, Rapier

import sim.core_feats
import sim.feat
import sim.character


class RogueLevel(sim.core_feats.ClassLevels):
    def __init__(self, level: int):
        super().__init__(name="Rogue", level=level)


class SneakAttack(sim.feat.Feat):
    def __init__(self, num):
        self.num = num

    def begin_turn(self, target):
        self.used = False

    def attack_result(self, args):
        if args.hits() and not self.used:
            self.used = True
            args.add_damage(source="SneakAttack", dice=self.num * [6])


class SteadyAim(sim.feat.Feat):
    def before_action(self, target):
        if self.character.use_bonus("SteadyAim"):
            self.enabled = True

    def attack_roll(self, args):
        if self.enabled:
            args.adv = True
            self.enabled = False

    def end_turn(self, target):
        self.enabled = False


class StrokeOfLuck(sim.feat.Feat):
    def begin_turn(self, target):
        self.used = False

    def attack_roll(self, args):
        if not self.used and args.roll() < 10:
            self.used = True
            args.roll1 = 20
            args.roll2 = 20


class Assassinate(sim.feat.Feat):
    def __init__(self, dmg):
        self.dmg = dmg
        self.adv = False

    def apply(self, character: "sim.character.Character"):
        super().apply(character)
        character.add_resource('Assassinate', max_uses=1, short_rest=True)

    def begin_turn(self, target):
        if self.character.resources['Assassinate'].has():
             if do_roll(adv=True) + self.character.mod("dex") > do_roll():
                self.adv = True

    def attack_roll(self, args):
        if self.adv:
            args.adv = True

    def attack_result(self, args):
        if args.hits() and self.character.resources['Assassinate'].use(detail="Assassinate", target=args.attack.target):
            args.add_damage(source="Assassinate", damage=self.dmg)

    def end_turn(self, target):
        self.adv = False


class DeathStrike(sim.feat.Feat):
    def apply(self, character: "sim.character.Character"):
        super().apply(character)
        character.add_resource('Death Strike', max_uses=1, short_rest=True)

    def attack_result(self, args):
        if args.hits() and self.character.resources['Death Strike'].use(detail="Death Strike", target=args.attack.target):
            if not args.attack.target.save("dex", self.character.dc("dex")):
                args.dmg_multiplier *= 2


class BoomingBladeAction(sim.feat.Feat):
    def __init__(
        self, character: "sim.character.Character", weapon: "sim.weapons.Weapon"
    ):
        self.weapon = weapon
        self.character = character

    def action(self, target):
        self.character.weapon_attack(
            target, self.weapon, tags=["main_action", "booming_blade"]
        )

    def attack_result(self, args):
        if args.misses() or not args.attack.has_tag("booming_blade"):
            return
        if self.character.level >= 17:
            extra_dice = 3
        elif self.character.level >= 11:
            extra_dice = 2
        elif self.character.level >= 5:
            extra_dice = 1
        else:
            return
        args.add_damage(source="BoomingBlade", dice=extra_dice * [8])


def rogue_feats(
    level: int,
    masteries: List["sim.weapons.WeaponMastery"],
    asis: Optional[List["sim.feat.Feat"]] = None,
):
    feats: List["sim.feat.Feat"] = []
    if level >= 1:
        feats.append(RogueLevel(level))
        feats.append(SneakAttack(math.ceil(level / 2)))
        feats.append(WeaponMasteries(masteries))
    # Level 2 (Cunning Action) is irrelevant for now
    if level >= 3:
        feats.append(SteadyAim())
    # Level 5 (Cunning Strike) is mostly useless for DPR
    # Level 7 (Evasion) is irrelevant
    # Level 7 (Reliable Talent) is irrelevant
    # Level 11 (Improved Cunning Strike) is unused
    # Level 14 (Devious Strikes) is unused (maybe Knock Out is useful?)
    # Level 15 (Slippery Mind) is irrelevant
    # Level 18 (Elusive) is irrelevant
    if level >= 20:
        feats.append(StrokeOfLuck())
    apply_asi_feats(level=level, feats=feats, asis=asis)
    return feats


def assassin_rogue_feats(level: int) -> List["sim.feat.Feat"]:
    feats: List["sim.feat.Feat"] = []
    if level >= 3:
        feats.append(Assassinate(level))
    # Level 3 (Assassin's Tools) is irrelevant
    # Level 9 (Infiltration Expertise) is irrelevant
    # TODO: Level 13 (Envenom Weapons)
    if level >= 17:
        feats.append(DeathStrike())
    return feats


class AssassinRogue(sim.character.Character):
    def __init__(self, level: int, **kwargs):
        self.name = "Assassin Rogue"
        magic_weapon = get_magic_weapon(level)
        feats: List["sim.feat.Feat"] = []

        shortsword = Shortsword(magic_bonus=magic_weapon)
        scimitar = Scimitar(magic_bonus=magic_weapon)
        feats.append(AttackAction(attacks=[shortsword], nick_attacks=[scimitar]))

        feats.extend(
            rogue_feats(
                level=level,
                masteries=["Vex", "Nick"],
                asis=[
                    ASI(["dex"]),
                    ASI(["dex", "wis"]),
                    ASI(),
                    ASI(),
                    IrresistibleOffense("dex"),
                ],
            )
        )
        feats.extend(assassin_rogue_feats(level))

        super().__init__(
            name=self.name,
            level=level,
            stats=[10, 17, 10, 10, 10, 10],
            base_feats=feats,
        )


class ArcaneTricksterRogue(sim.character.Character):
    def __init__(self, level, **kwargs):
        self.name = "Arcane Trickster Rogue"
        magic_weapon = get_magic_weapon(level)
        feats = []
        if level >= 5:
            rapier = Rapier(magic_bonus=magic_weapon)
            feats.append(BoomingBladeAction(self, rapier))
        else:
            shortsword = Shortsword(magic_bonus=magic_weapon)
            scimitar = Scimitar(magic_bonus=magic_weapon)
            feats.append(AttackAction(attacks=[shortsword], nick_attacks=[scimitar]))
        feats.extend(
            rogue_feats(
                level=level,
                masteries=["Vex", "Nick"],
                asis=[
                    ASI(["dex"]),
                    ASI(["dex", "wis"]),
                    ASI(),
                    ASI(),
                    IrresistibleOffense("dex"),
                ],
            )
        )
        # TODO: Arcane Trickster feats
        super().__init__(
            name=self.name,
            level=level,
            stats=[10, 17, 10, 10, 10, 10],
            base_feats=feats,
        )
