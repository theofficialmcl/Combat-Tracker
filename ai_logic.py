from __future__ import annotations

import random
from typing import Optional

from models import Combatant
from combat_engine import CombatEngine
from battlefield import legal_movement_positions


def random_ai_turn(engine: CombatEngine) -> str:
    actor = engine.current_actor()
    if actor is None or not actor.is_alive:
        return f"{actor.name if actor else 'Unknown'} cannot act."

    legal_moves = legal_movement_positions(actor, engine.battlefield, engine.combatants)
    if legal_moves:
        actor.position = random.choice(legal_moves)

    actor_spells = [engine.spell_lookup[name] for name in actor.spell_names if name in engine.spell_lookup]
    usable_attacks = actor.attacks[:]

    action_pool = []

    for attack in usable_attacks:
        targets = engine.legal_targets_for_attack(actor, attack)
        for t in targets:
            action_pool.append(("attack", attack, t))

    for spell in actor_spells:
        targets = engine.legal_targets_for_spell(actor, spell)
        for t in targets:
            action_pool.append(("spell", spell, t))

    if not action_pool:
        return f"{actor.name} moves but has no legal target."

    kind, payload, target = random.choice(action_pool)

    if kind == "attack":
        return engine.resolve_attack(actor, target, payload)
    return engine.resolve_spell(actor, payload, target)
