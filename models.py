from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
DAMAGE_TYPES = [
    "none", "acid", "bludgeoning", "cold", "fire", "force", "lightning",
    "necrotic", "piercing", "poison", "psychic", "radiant", "slashing", "thunder"
]
TARGET_MODES = ["single", "aoe_all_enemies"]


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Attack:
    name: str
    stat_used: str
    attack_bonus: int
    num_dice: int
    die_size: int
    damage_bonus: int = 0
    damage_type: str = "none"
    range_ft: int = 5
    range_desc: str = "melee"

    @property
    def to_hit(self) -> int:
        return self.attack_bonus


@dataclass
class Spell:
    name: str
    level: int
    num_dice: int
    die_size: int
    damage_bonus: int
    save_dc: int
    save_stat: str
    half_on_save: bool
    damage_type: str = "none"
    target_mode: str = "single"
    range_ft: int = 60
    aoe_radius_ft: int = 0


@dataclass
class Combatant:
    name: str
    side: str
    ac: int
    max_hp: int
    hp: int
    movement: int
    stats: Dict[str, int]
    saves: Dict[str, int]
    attacks: List[Attack] = field(default_factory=list)
    spell_names: List[str] = field(default_factory=list)
    initiative_bonus: int = 0
    is_alive: bool = True
    conditions: List[str] = field(default_factory=list)
    position: Position = field(default_factory=lambda: Position(0, 0))

    def hp_pct(self) -> float:
        return 0.0 if self.max_hp <= 0 else self.hp / self.max_hp

    @property
    def move_squares(self) -> int:
        return max(0, self.movement // 5)


@dataclass
class TurnEvent:
    round_num: int
    actor: str
    description: str


@dataclass
class BattlefieldMap:
    name: str
    width: int
    height: int
