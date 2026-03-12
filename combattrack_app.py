from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import random
import copy

import pandas as pd
import streamlit as st


# ============================================================
# CONFIG / STYLING
# ============================================================
st.set_page_config(page_title="Combat Simulator", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0f14;
        color: #e8eef2;
    }
    section[data-testid="stSidebar"] {
        background-color: #11161d;
    }
    .stMarkdown, .stText, label, p, h1, h2, h3, h4, h5, h6, div {
        color: #e8eef2;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea, input {
        background-color: #18202a !important;
        color: #e8eef2 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA MODELS
# ============================================================
ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
DAMAGE_TYPES = [
    "none", "acid", "bludgeoning", "cold", "fire", "force", "lightning",
    "necrotic", "piercing", "poison", "psychic", "radiant", "slashing", "thunder"
]


@dataclass
class Attack:
    name: str
    to_hit: int
    num_dice: int
    die_size: int
    damage_bonus: int = 0
    damage_type: str = "none"
    range_desc: str = "melee"


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
    target_mode: str = "single"  # single / aoe_all_enemies


@dataclass
class Combatant:
    name: str
    side: str  # PCs or Monsters
    ac: int
    max_hp: int
    hp: int
    stats: Dict[str, int]
    saves: Dict[str, int]
    attacks: List[Attack] = field(default_factory=list)
    spells: List[Spell] = field(default_factory=list)
    initiative_bonus: int = 0
    is_alive: bool = True
    conditions: List[str] = field(default_factory=list)

    def hp_pct(self) -> float:
        return 0 if self.max_hp <= 0 else self.hp / self.max_hp


@dataclass
class TurnEvent:
    round_num: int
    actor: str
    description: str


# ============================================================
# SAMPLE DATABASES
# ============================================================
def starter_pc_database() -> List[Combatant]:
    return [
        Combatant(
            name="Fighter",
            side="PCs",
            ac=18,
            max_hp=52,
            hp=52,
            stats={"STR": 18, "DEX": 12, "CON": 16, "INT": 10, "WIS": 12, "CHA": 10},
            saves={"STR": 7, "DEX": 1, "CON": 6, "INT": 0, "WIS": 1, "CHA": 0},
            initiative_bonus=1,
            attacks=[Attack("Longsword", to_hit=8, num_dice=1, die_size=8, damage_bonus=5, damage_type="slashing")],
            spells=[],
        ),
        Combatant(
            name="Wizard",
            side="PCs",
            ac=14,
            max_hp=34,
            hp=34,
            stats={"STR": 8, "DEX": 14, "CON": 14, "INT": 18, "WIS": 12, "CHA": 10},
            saves={"STR": -1, "DEX": 2, "CON": 2, "INT": 7, "WIS": 1, "CHA": 0},
            initiative_bonus=2,
            attacks=[Attack("Fire Bolt", to_hit=7, num_dice=2, die_size=10, damage_bonus=0, damage_type="fire", range_desc="ranged")],
            spells=[
                Spell("Fireball", level=3, num_dice=8, die_size=6, damage_bonus=0, save_dc=15, save_stat="DEX", half_on_save=True, damage_type="fire", target_mode="aoe_all_enemies"),
                Spell("Mind Spike", level=2, num_dice=3, die_size=8, damage_bonus=0, save_dc=15, save_stat="WIS", half_on_save=False, damage_type="psychic", target_mode="single"),
            ],
        ),
    ]


def starter_monster_database() -> List[Combatant]:
    return [
        Combatant(
            name="Ogre",
            side="Monsters",
            ac=11,
            max_hp=59,
            hp=59,
            stats={"STR": 19, "DEX": 8, "CON": 16, "INT": 5, "WIS": 7, "CHA": 7},
            saves={"STR": 4, "DEX": -1, "CON": 3, "INT": -3, "WIS": -2, "CHA": -2},
            initiative_bonus=-1,
            attacks=[Attack("Greatclub", to_hit=6, num_dice=2, die_size=8, damage_bonus=4, damage_type="bludgeoning")],
            spells=[],
        ),
        Combatant(
            name="Cult Mage",
            side="Monsters",
            ac=12,
            max_hp=40,
            hp=40,
            stats={"STR": 9, "DEX": 14, "CON": 12, "INT": 16, "WIS": 13, "CHA": 11},
            saves={"STR": -1, "DEX": 2, "CON": 1, "INT": 5, "WIS": 1, "CHA": 0},
            initiative_bonus=2,
            attacks=[Attack("Dagger", to_hit=4, num_dice=1, die_size=4, damage_bonus=2, damage_type="piercing")],
            spells=[
                Spell("Burning Hands", level=1, num_dice=3, die_size=6, damage_bonus=0, save_dc=13, save_stat="DEX", half_on_save=True, damage_type="fire", target_mode="aoe_all_enemies"),
                Spell("Ray of Sickness", level=1, num_dice=2, die_size=8, damage_bonus=0, save_dc=13, save_stat="CON", half_on_save=False, damage_type="poison", target_mode="single"),
            ],
        ),
    ]


# ============================================================
# STATE HELPERS
# ============================================================
def ensure_state() -> None:
    if "pc_db" not in st.session_state:
        st.session_state.pc_db = starter_pc_database()
    if "monster_db" not in st.session_state:
        st.session_state.monster_db = starter_monster_database()
    if "selected_pcs" not in st.session_state:
        st.session_state.selected_pcs = [c.name for c in st.session_state.pc_db]
    if "selected_monsters" not in st.session_state:
        st.session_state.selected_monsters = [c.name for c in st.session_state.monster_db]
    if "combat" not in st.session_state:
        st.session_state.combat = None


# ============================================================
# DICE / COMBAT MATH
# ============================================================
def roll_d20() -> int:
    return random.randint(1, 20)


def roll_damage(num_dice: int, die_size: int, bonus: int = 0) -> int:
    return sum(random.randint(1, die_size) for _ in range(num_dice)) + bonus


def attack_hits(attacker: Combatant, target: Combatant, attack: Attack) -> Tuple[bool, int, int]:
    roll = roll_d20()
    total = roll + attack.to_hit
    return total >= target.ac, roll, total


def saving_throw(target: Combatant, save_stat: str, dc: int) -> Tuple[bool, int, int]:
    roll = roll_d20()
    bonus = target.saves.get(save_stat, 0)
    total = roll + bonus
    return total >= dc, roll, total


def apply_damage(target: Combatant, dmg: int) -> int:
    actual = max(0, dmg)
    target.hp = max(0, target.hp - actual)
    if target.hp <= 0:
        target.is_alive = False
    return actual


def living(combatants: List[Combatant], side: Optional[str] = None) -> List[Combatant]:
    result = [c for c in combatants if c.is_alive]
    if side is not None:
        result = [c for c in result if c.side == side]
    return result


def choose_target(actor: Combatant, combatants: List[Combatant]) -> Optional[Combatant]:
    enemies = living(combatants, "Monsters" if actor.side == "PCs" else "PCs")
    if not enemies:
        return None
    # Simple AI: lowest HP enemy
    return sorted(enemies, key=lambda c: (c.hp, c.max_hp))[0]


def choose_action(actor: Combatant, combatants: List[Combatant]) -> Tuple[str, object]:
    enemies = living(combatants, "Monsters" if actor.side == "PCs" else "PCs")
    if not enemies:
        return ("none", None)

    if actor.spells:
        # Basic AI: if there are multiple enemies alive and actor has an AOE, use first AOE spell.
        if len(enemies) >= 2:
            for spell in actor.spells:
                if spell.target_mode == "aoe_all_enemies":
                    return ("spell", spell)
        return ("spell", actor.spells[0])

    if actor.attacks:
        return ("attack", actor.attacks[0])

    return ("none", None)


def run_attack(actor: Combatant, combatants: List[Combatant], attack: Attack) -> str:
    target = choose_target(actor, combatants)
    if not target:
        return f"{actor.name} has no valid targets."

    hit, raw_roll, total = attack_hits(actor, target, attack)
    if not hit:
        return f"{actor.name} uses {attack.name} on {target.name}: miss ({raw_roll}+{attack.to_hit}={total} vs AC {target.ac})."

    dmg = roll_damage(attack.num_dice, attack.die_size, attack.damage_bonus)
    actual = apply_damage(target, dmg)
    suffix = " and drops them to 0 HP" if not target.is_alive else ""
    return (
        f"{actor.name} uses {attack.name} on {target.name}: hit ({raw_roll}+{attack.to_hit}={total} vs AC {target.ac}) "
        f"for {actual} {attack.damage_type} damage. {target.name} is at {target.hp}/{target.max_hp} HP{suffix}."
    )


def run_spell_single(actor: Combatant, combatants: List[Combatant], spell: Spell) -> str:
    target = choose_target(actor, combatants)
    if not target:
        return f"{actor.name} has no valid targets."

    saved, raw_roll, total = saving_throw(target, spell.save_stat, spell.save_dc)
    dmg = roll_damage(spell.num_dice, spell.die_size, spell.damage_bonus)

    if saved:
        final = dmg // 2 if spell.half_on_save else 0
        actual = apply_damage(target, final)
        suffix = " and drops them to 0 HP" if not target.is_alive else ""
        return (
            f"{actor.name} casts {spell.name} on {target.name}. {target.name} saves "
            f"({raw_roll}+{target.saves.get(spell.save_stat, 0)}={total} vs DC {spell.save_dc}) "
            f"and takes {actual} {spell.damage_type} damage{suffix}."
        )

    actual = apply_damage(target, dmg)
    suffix = " and drops them to 0 HP" if not target.is_alive else ""
    return (
        f"{actor.name} casts {spell.name} on {target.name}. {target.name} fails "
        f"({raw_roll}+{target.saves.get(spell.save_stat, 0)}={total} vs DC {spell.save_dc}) "
        f"and takes {actual} {spell.damage_type} damage{suffix}."
    )


def run_spell_aoe(actor: Combatant, combatants: List[Combatant], spell: Spell) -> str:
    enemies = living(combatants, "Monsters" if actor.side == "PCs" else "PCs")
    if not enemies:
        return f"{actor.name} has no valid targets."

    chunks = []
    for target in enemies:
        saved, raw_roll, total = saving_throw(target, spell.save_stat, spell.save_dc)
        dmg = roll_damage(spell.num_dice, spell.die_size, spell.damage_bonus)
        final = dmg // 2 if (saved and spell.half_on_save) else (0 if saved else dmg)
        actual = apply_damage(target, final)
        result_word = "saves" if saved else "fails"
        down = ", drops to 0 HP" if not target.is_alive else f", {target.hp}/{target.max_hp} HP left"
        chunks.append(
            f"{target.name} {result_word} ({raw_roll}+{target.saves.get(spell.save_stat, 0)}={total} vs DC {spell.save_dc}) "
            f"and takes {actual} {spell.damage_type}{down}"
        )

    return f"{actor.name} casts {spell.name}: " + "; ".join(chunks) + "."


def execute_turn(actor: Combatant, combatants: List[Combatant]) -> str:
    if not actor.is_alive:
        return f"{actor.name} is down and cannot act."

    kind, payload = choose_action(actor, combatants)
    if kind == "attack":
        return run_attack(actor, combatants, payload)
    if kind == "spell":
        spell: Spell = payload
        if spell.target_mode == "aoe_all_enemies":
            return run_spell_aoe(actor, combatants, spell)
        return run_spell_single(actor, combatants, spell)
    return f"{actor.name} has no usable action."


def roll_initiative(combatants: List[Combatant]) -> List[Tuple[int, int, Combatant]]:
    order = []
    for c in combatants:
        roll = roll_d20()
        total = roll + c.initiative_bonus
        order.append((total, c.initiative_bonus, c))
    order.sort(key=lambda x: (x[0], x[1], x[2].stats.get("DEX", 0)), reverse=True)
    return order


def snapshot_hp(combatants: List[Combatant], round_num: int) -> pd.DataFrame:
    rows = []
    for c in combatants:
        rows.append(
            {
                "Round": round_num,
                "Name": c.name,
                "Side": c.side,
                "HP": c.hp,
                "Max HP": c.max_hp,
                "Alive": c.is_alive,
            }
        )
    return pd.DataFrame(rows)


# ============================================================
# COMBAT ENGINE
# ============================================================
class CombatEngine:
    def __init__(self, combatants: List[Combatant]):
        self.combatants: List[Combatant] = copy.deepcopy(combatants)
        self.round_num: int = 1
        self.order: List[Tuple[int, int, Combatant]] = roll_initiative(self.combatants)
        self.turn_index: int = 0
        self.log: List[TurnEvent] = []
        self.hp_history: List[pd.DataFrame] = [snapshot_hp(self.combatants, 0)]
        self.finished: bool = False
        self.winner: Optional[str] = None

    def current_actor(self) -> Optional[Combatant]:
        if self.finished or not self.order:
            return None
        return self.order[self.turn_index][2]

    def check_end(self) -> None:
        pcs_alive = len(living(self.combatants, "PCs"))
        monsters_alive = len(living(self.combatants, "Monsters"))
        if pcs_alive == 0:
            self.finished = True
            self.winner = "Monsters"
        elif monsters_alive == 0:
            self.finished = True
            self.winner = "PCs"

    def step_turn(self) -> None:
        if self.finished:
            return

        actor = self.current_actor()
        if actor is None:
            return

        desc = execute_turn(actor, self.combatants)
        self.log.append(TurnEvent(self.round_num, actor.name, desc))
        self.check_end()
        self.hp_history.append(snapshot_hp(self.combatants, self.round_num))

        if self.finished:
            return

        self.turn_index += 1
        if self.turn_index >= len(self.order):
            self.turn_index = 0
            self.round_num += 1
            # keep dead combatants in order; they simply skip on future turns

    def run_to_completion(self, max_rounds: int = 50) -> None:
        safety = 0
        while not self.finished and safety < max_rounds * max(1, len(self.order)):
            self.step_turn()
            safety += 1
        self.check_end()
        if not self.finished:
            self.finished = True
            self.winner = "No result (round cap)"


# ============================================================
# UI HELPERS
# ============================================================
def combatant_editor(side: str) -> None:
    db_key = "pc_db" if side == "PCs" else "monster_db"
    db: List[Combatant] = st.session_state[db_key]

    st.subheader(f"{side} Database")
    for idx, combatant in enumerate(db):
        with st.expander(f"{combatant.name} ({side})", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                combatant.name = st.text_input("Name", value=combatant.name, key=f"{side}_name_{idx}")
                combatant.ac = st.number_input("AC", min_value=1, max_value=40, value=combatant.ac, key=f"{side}_ac_{idx}")
                combatant.max_hp = st.number_input("Max HP", min_value=1, max_value=999, value=combatant.max_hp, key=f"{side}_maxhp_{idx}")
                combatant.hp = st.number_input("Current HP", min_value=0, max_value=999, value=min(combatant.hp, combatant.max_hp), key=f"{side}_hp_{idx}")
                combatant.initiative_bonus = st.number_input("Initiative Bonus", min_value=-10, max_value=20, value=combatant.initiative_bonus, key=f"{side}_init_{idx}")
            with c2:
                st.markdown("**Stats**")
                for ab in ABILITIES:
                    combatant.stats[ab] = st.number_input(f"{ab} Stat", min_value=1, max_value=30, value=combatant.stats[ab], key=f"{side}_{idx}_stat_{ab}")
            with c3:
                st.markdown("**Saves**")
                for ab in ABILITIES:
                    combatant.saves[ab] = st.number_input(f"{ab} Save", min_value=-10, max_value=20, value=combatant.saves[ab], key=f"{side}_{idx}_save_{ab}")

            st.markdown("**Attacks**")
            for a_idx, attack in enumerate(combatant.attacks):
                cols = st.columns(7)
                attack.name = cols[0].text_input("Attack", value=attack.name, key=f"{side}_{idx}_atk_name_{a_idx}")
                attack.to_hit = cols[1].number_input("To Hit", min_value=-10, max_value=20, value=attack.to_hit, key=f"{side}_{idx}_atk_hit_{a_idx}")
                attack.num_dice = cols[2].number_input("Dice", min_value=1, max_value=20, value=attack.num_dice, key=f"{side}_{idx}_atk_x_{a_idx}")
                attack.die_size = cols[3].number_input("Die", min_value=2, max_value=20, value=attack.die_size, key=f"{side}_{idx}_atk_y_{a_idx}")
                attack.damage_bonus = cols[4].number_input("Bonus", min_value=-10, max_value=50, value=attack.damage_bonus, key=f"{side}_{idx}_atk_bonus_{a_idx}")
                attack.damage_type = cols[5].selectbox("Type", DAMAGE_TYPES, index=DAMAGE_TYPES.index(attack.damage_type), key=f"{side}_{idx}_atk_type_{a_idx}")
                attack.range_desc = cols[6].text_input("Range", value=attack.range_desc, key=f"{side}_{idx}_atk_range_{a_idx}")
            if st.button("Add Attack", key=f"{side}_{idx}_add_attack"):
                combatant.attacks.append(Attack("New Attack", 5, 1, 8, 3, "slashing", "melee"))
                st.rerun()

            st.markdown("**Spells**")
            for s_idx, spell in enumerate(combatant.spells):
                cols1 = st.columns(6)
                spell.name = cols1[0].text_input("Spell", value=spell.name, key=f"{side}_{idx}_spell_name_{s_idx}")
                spell.level = cols1[1].number_input("Level", min_value=0, max_value=9, value=spell.level, key=f"{side}_{idx}_spell_lvl_{s_idx}")
                spell.num_dice = cols1[2].number_input("Dice", min_value=1, max_value=30, value=spell.num_dice, key=f"{side}_{idx}_spell_x_{s_idx}")
                spell.die_size = cols1[3].number_input("Die", min_value=2, max_value=20, value=spell.die_size, key=f"{side}_{idx}_spell_y_{s_idx}")
                spell.damage_bonus = cols1[4].number_input("Bonus", min_value=-10, max_value=50, value=spell.damage_bonus, key=f"{side}_{idx}_spell_bonus_{s_idx}")
                spell.damage_type = cols1[5].selectbox("Type", DAMAGE_TYPES, index=DAMAGE_TYPES.index(spell.damage_type), key=f"{side}_{idx}_spell_type_{s_idx}")

                cols2 = st.columns(5)
                spell.save_dc = cols2[0].number_input("Save DC", min_value=1, max_value=30, value=spell.save_dc, key=f"{side}_{idx}_spell_dc_{s_idx}")
                spell.save_stat = cols2[1].selectbox("Save Stat", ABILITIES, index=ABILITIES.index(spell.save_stat), key=f"{side}_{idx}_spell_stat_{s_idx}")
                spell.half_on_save = cols2[2].checkbox("Half on Save", value=spell.half_on_save, key=f"{side}_{idx}_spell_half_{s_idx}")
                spell.target_mode = cols2[3].selectbox("Targeting", ["single", "aoe_all_enemies"], index=0 if spell.target_mode == "single" else 1, key=f"{side}_{idx}_spell_target_{s_idx}")
                cols2[4].markdown("<br>", unsafe_allow_html=True)
            if st.button("Add Spell", key=f"{side}_{idx}_add_spell"):
                combatant.spells.append(Spell("New Spell", 1, 3, 6, 0, 13, "DEX", True, "fire", "single"))
                st.rerun()

    if st.button(f"Add New {side[:-1] if side.endswith('s') else side}", key=f"add_new_{side}"):
        db.append(
            Combatant(
                name=f"New {side[:-1]}",
                side=side,
                ac=12,
                max_hp=20,
                hp=20,
                stats={ab: 10 for ab in ABILITIES},
                saves={ab: 0 for ab in ABILITIES},
                attacks=[Attack("Basic Attack", 4, 1, 6, 2, "slashing", "melee")],
                spells=[],
                initiative_bonus=0,
            )
        )
        st.rerun()


def display_initiative(engine: CombatEngine) -> None:
    rows = []
    for idx, (init_total, bonus, c) in enumerate(engine.order):
        rows.append(
            {
                "Order": idx + 1,
                "Name": c.name,
                "Side": c.side,
                "Init Total": init_total,
                "Init Bonus": bonus,
                "Alive": c.is_alive,
                "Current Turn": idx == engine.turn_index and not engine.finished,
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def display_hp_panel(engine: CombatEngine) -> None:
    pcs = [c for c in engine.combatants if c.side == "PCs"]
    monsters = [c for c in engine.combatants if c.side == "Monsters"]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### PCs")
        for c in pcs:
            bar = max(0.0, min(1.0, c.hp_pct()))
            st.progress(bar, text=f"{c.name}: {c.hp}/{c.max_hp} HP{' (down)' if not c.is_alive else ''}")
    with c2:
        st.markdown("### Monsters")
        for c in monsters:
            bar = max(0.0, min(1.0, c.hp_pct()))
            st.progress(bar, text=f"{c.name}: {c.hp}/{c.max_hp} HP{' (down)' if not c.is_alive else ''}")


def display_log(engine: CombatEngine) -> None:
    st.markdown("### Combat Log")
    if not engine.log:
        st.info("No actions taken yet.")
        return
    for event in engine.log[-20:]:
        st.markdown(f"**Round {event.round_num} — {event.actor}:** {event.description}")


def display_round_history(engine: CombatEngine) -> None:
    st.markdown("### HP After Each Round / Turn Snapshot")
    if not engine.hp_history:
        return
    hist = pd.concat(engine.hp_history, ignore_index=True)
    st.dataframe(hist, use_container_width=True)


# ============================================================
# MAIN UI
# ============================================================
ensure_state()

st.title("Combat Simulator")
st.caption("Load PCs and monsters, roll initiative, and simulate combat turn by turn or to completion.")

tab1, tab2, tab3 = st.tabs(["Databases", "Encounter Builder", "Combat"])

with tab1:
    sub1, sub2 = st.tabs(["PCs", "Monsters"])
    with sub1:
        combatant_editor("PCs")
    with sub2:
        combatant_editor("Monsters")

with tab2:
    st.subheader("Choose Combatants for the Encounter")

    pc_names = [c.name for c in st.session_state.pc_db]
    monster_names = [c.name for c in st.session_state.monster_db]

    st.session_state.selected_pcs = st.multiselect(
        "Select PCs",
        options=pc_names,
        default=st.session_state.selected_pcs,
    )
    st.session_state.selected_monsters = st.multiselect(
        "Select Monsters",
        options=monster_names,
        default=st.session_state.selected_monsters,
    )

    if st.button("Start New Combat"):
        chosen: List[Combatant] = []
        chosen.extend([copy.deepcopy(c) for c in st.session_state.pc_db if c.name in st.session_state.selected_pcs])
        chosen.extend([copy.deepcopy(c) for c in st.session_state.monster_db if c.name in st.session_state.selected_monsters])

        for c in chosen:
            c.hp = c.max_hp
            c.is_alive = c.hp > 0
            c.conditions = []

        if len(chosen) < 2:
            st.warning("Select at least two combatants.")
        elif not any(c.side == "PCs" for c in chosen) or not any(c.side == "Monsters" for c in chosen):
            st.warning("You need at least one PC and one monster.")
        else:
            st.session_state.combat = CombatEngine(chosen)
            st.success("Combat initialized.")

with tab3:
    engine: Optional[CombatEngine] = st.session_state.combat

    if engine is None:
        st.info("Build an encounter and start combat first.")
    else:
        c_top1, c_top2 = st.columns([2, 1])
        with c_top1:
            st.markdown(f"## Round {engine.round_num}")
            actor = engine.current_actor()
            if engine.finished:
                st.success(f"Combat finished. Winner: {engine.winner}")
            elif actor is not None:
                st.info(f"Current turn: {actor.name} ({actor.side})")
        with c_top2:
            st.markdown("### Controls")
            if st.button("Run Next Turn", use_container_width=True, disabled=engine.finished):
                engine.step_turn()
                st.rerun()
            if st.button("Run to Completion", use_container_width=True, disabled=engine.finished):
                engine.run_to_completion()
                st.rerun()
            if st.button("Reset Combat", use_container_width=True):
                st.session_state.combat = None
                st.rerun()

        display_hp_panel(engine)

        with st.expander("Initiative Order", expanded=True):
            display_initiative(engine)

        display_log(engine)

        with st.expander("HP History", expanded=False):
            display_round_history(engine)

        with st.expander("HP History", expanded=False):
            display_round_history(engine)
