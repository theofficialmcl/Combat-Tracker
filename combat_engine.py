from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import copy
import random
import pandas as pd

from models import Combatant, Attack, Spell, TurnEvent, BattlefieldMap, Position
from battlefield import attack_in_range, legal_movement_positions, distance_in_feet, spell_targets_in_radius


def roll_d20() -> int:
    return random.randint(1, 20)


def roll_damage(num_dice: int, die_size: int, bonus: int = 0) -> int:
    return sum(random.randint(1, die_size) for _ in range(num_dice)) + bonus


def living(combatants: List[Combatant], side: Optional[str] = None) -> List[Combatant]:
    result = [c for c in combatants if c.is_alive]
    if side is not None:
        result = [c for c in result if c.side == side]
    return result


def apply_damage(target: Combatant, dmg: int) -> int:
    actual = max(0, dmg)
    target.hp = max(0, target.hp - actual)
    if target.hp <= 0:
        target.is_alive = False
    return actual


def saving_throw(target: Combatant, save_stat: str, dc: int) -> Tuple[bool, int, int]:
    roll = roll_d20()
    bonus = target.saves.get(save_stat, 0)
    total = roll + bonus
    return total >= dc, roll, total


def snapshot_hp(combatants: List[Combatant], round_num: int) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Round": round_num,
            "Name": c.name,
            "Side": c.side,
            "HP": c.hp,
            "Max HP": c.max_hp,
            "Alive": c.is_alive,
            "X": c.position.x,
            "Y": c.position.y,
        }
        for c in combatants
    ])


@dataclass
class CombatEngine:
    combatants: List[Combatant]
    battlefield: BattlefieldMap
    spell_lookup: dict[str, Spell]

    def __post_init__(self):
        self.combatants = copy.deepcopy(self.combatants)
        self.round_num = 1
        self.order = self.roll_initiative()
        self.turn_index = 0
        self.log: List[TurnEvent] = []
        self.hp_history = [snapshot_hp(self.combatants, 0)]
        self.finished = False
        self.winner: Optional[str] = None

    def roll_initiative(self):
        rows = []
        for c in self.combatants:
            roll = roll_d20()
            total = roll + c.initiative_bonus
            rows.append((total, c.initiative_bonus, c))
        rows.sort(key=lambda x: (x[0], x[1], x[2].stats.get("DEX", 0)), reverse=True)
        return rows

    def current_actor(self) -> Optional[Combatant]:
        if self.finished or not self.order:
            return None
        return self.order[self.turn_index][2]

    def check_end(self):
        pcs_alive = len(living(self.combatants, "PCs"))
        monsters_alive = len(living(self.combatants, "Monsters"))
        if pcs_alive == 0:
            self.finished = True
            self.winner = "Monsters"
        elif monsters_alive == 0:
            self.finished = True
            self.winner = "PCs"

    def legal_targets_for_attack(self, actor: Combatant, attack: Attack) -> List[Combatant]:
        enemy_side = "Monsters" if actor.side == "PCs" else "PCs"
        enemies = living(self.combatants, enemy_side)
        return [e for e in enemies if attack_in_range(actor, e, attack.range_ft)]

    def legal_targets_for_spell(self, actor: Combatant, spell: Spell) -> List[Combatant]:
        enemy_side = "Monsters" if actor.side == "PCs" else "PCs"
        enemies = living(self.combatants, enemy_side)
        return [e for e in enemies if attack_in_range(actor, e, spell.range_ft)]

    def move_actor(self, actor: Combatant, new_pos: Position) -> str:
        actor.position = Position(new_pos.x, new_pos.y)
        return f"{actor.name} moves to ({actor.position.x}, {actor.position.y})."

    def resolve_attack(self, actor: Combatant, target: Combatant, attack: Attack) -> str:
        roll = roll_d20()
        total = roll + attack.to_hit
        if total < target.ac:
            return f"{actor.name} attacks {target.name} with {attack.name}: miss ({roll}+{attack.to_hit}={total} vs AC {target.ac})."
        dmg = roll_damage(attack.num_dice, attack.die_size, attack.damage_bonus)
        actual = apply_damage(target, dmg)
        return f"{actor.name} hits {target.name} with {attack.name} for {actual} {attack.damage_type}. {target.name}: {target.hp}/{target.max_hp} HP."

    def resolve_spell(self, actor: Combatant, spell: Spell, target: Combatant) -> str:
        saved, raw_roll, total = saving_throw(target, spell.save_stat, spell.save_dc)
        dmg = roll_damage(spell.num_dice, spell.die_size, spell.damage_bonus)
        final = dmg // 2 if (saved and spell.half_on_save) else (0 if saved else dmg)
        actual = apply_damage(target, final)
        result = "saves" if saved else "fails"
        return (
            f"{actor.name} casts {spell.name} on {target.name}. "
            f"{target.name} {result} ({raw_roll}+{target.saves.get(spell.save_stat, 0)}={total} vs DC {spell.save_dc}) "
            f"and takes {actual} {spell.damage_type}. {target.name}: {target.hp}/{target.max_hp} HP."
        )

    def step_turn(self, description: str):
        actor = self.current_actor()
        if actor is None:
            return
        self.log.append(TurnEvent(self.round_num, actor.name, description))
        self.check_end()
        self.hp_history.append(snapshot_hp(self.combatants, self.round_num))
        if self.finished:
            return
        self.turn_index += 1
        if self.turn_index >= len(self.order):
            self.turn_index = 0
            self.round_num += 1
