from __future__ import annotations

from models import Combatant, Attack, Spell, BattlefieldMap, Position


def starter_spell_database() -> list[Spell]:
    return [
        Spell("Fireball", 3, 8, 6, 0, 15, "DEX", True, "fire", "single", range_ft=150, aoe_radius_ft=20),
        Spell("Mind Spike", 2, 3, 8, 0, 15, "WIS", False, "psychic", "single", range_ft=60, aoe_radius_ft=0),
        Spell("Burning Hands", 1, 3, 6, 0, 13, "DEX", True, "fire", "single", range_ft=15, aoe_radius_ft=15),
        Spell("Ray of Sickness", 1, 2, 8, 0, 13, "CON", False, "poison", "single", range_ft=60, aoe_radius_ft=0),
    ]


def starter_pc_database() -> list[Combatant]:
    return [
        Combatant(
            name="Fighter",
            side="PCs",
            ac=18,
            max_hp=52,
            hp=52,
            movement=30,
            stats={"STR": 18, "DEX": 12, "CON": 16, "INT": 10, "WIS": 12, "CHA": 10},
            saves={"STR": 7, "DEX": 1, "CON": 6, "INT": 0, "WIS": 1, "CHA": 0},
            initiative_bonus=1,
            attacks=[Attack("Longsword", "STR", 8, 1, 8, 5, "slashing", 5, "melee")],
            spell_names=[],
            position=Position(1, 1),
        ),
        Combatant(
            name="Wizard",
            side="PCs",
            ac=14,
            max_hp=34,
            hp=34,
            movement=30,
            stats={"STR": 8, "DEX": 14, "CON": 14, "INT": 18, "WIS": 12, "CHA": 10},
            saves={"STR": -1, "DEX": 2, "CON": 2, "INT": 7, "WIS": 1, "CHA": 0},
            initiative_bonus=2,
            attacks=[Attack("Fire Bolt", "INT", 7, 2, 10, 0, "fire", 120, "ranged")],
            spell_names=["Fireball", "Mind Spike"],
            position=Position(1, 2),
        ),
    ]


def starter_monster_database() -> list[Combatant]:
    return [
        Combatant(
            name="Ogre",
            side="Monsters",
            ac=11,
            max_hp=59,
            hp=59,
            movement=40,
            stats={"STR": 19, "DEX": 8, "CON": 16, "INT": 5, "WIS": 7, "CHA": 7},
            saves={"STR": 4, "DEX": -1, "CON": 3, "INT": -3, "WIS": -2, "CHA": -2},
            initiative_bonus=-1,
            attacks=[Attack("Greatclub", "STR", 6, 2, 8, 4, "bludgeoning", 5, "melee")],
            spell_names=[],
            position=Position(8, 1),
        ),
        Combatant(
            name="Cult Mage",
            side="Monsters",
            ac=12,
            max_hp=40,
            hp=40,
            movement=30,
            stats={"STR": 9, "DEX": 14, "CON": 12, "INT": 16, "WIS": 13, "CHA": 11},
            saves={"STR": -1, "DEX": 2, "CON": 1, "INT": 5, "WIS": 1, "CHA": 0},
            initiative_bonus=2,
            attacks=[Attack("Dagger", "DEX", 4, 1, 4, 2, "piercing", 5, "melee")],
            spell_names=["Burning Hands", "Ray of Sickness"],
            position=Position(8, 2),
        ),
    ]


def starter_maps() -> list[BattlefieldMap]:
    return [
        BattlefieldMap("Small Arena", 10, 8),
        BattlefieldMap("Roadside Fight", 14, 10),
        BattlefieldMap("Open Field", 20, 14),
    ]
