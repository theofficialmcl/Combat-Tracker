from __future__ import annotations

from typing import List, Optional, Tuple
from models import Combatant, Position, BattlefieldMap


def manhattan_distance(a: Position, b: Position) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def squares_in_range(origin: Position, move_squares: int, width: int, height: int) -> List[Position]:
    results: List[Position] = []
    for x in range(width):
        for y in range(height):
            pos = Position(x, y)
            if manhattan_distance(origin, pos) <= move_squares:
                results.append(pos)
    return results


def in_bounds(pos: Position, battlefield: BattlefieldMap) -> bool:
    return 0 <= pos.x < battlefield.width and 0 <= pos.y < battlefield.height


def occupied_positions(combatants: List[Combatant]) -> dict[Tuple[int, int], Combatant]:
    return {
        (c.position.x, c.position.y): c
        for c in combatants
        if c.is_alive
    }


def is_square_open(pos: Position, battlefield: BattlefieldMap, combatants: List[Combatant]) -> bool:
    if not in_bounds(pos, battlefield):
        return False
    occ = occupied_positions(combatants)
    return (pos.x, pos.y) not in occ


def legal_movement_positions(actor: Combatant, battlefield: BattlefieldMap, combatants: List[Combatant]) -> List[Position]:
    candidates = squares_in_range(actor.position, actor.move_squares, battlefield.width, battlefield.height)
    results: List[Position] = []
    for pos in candidates:
        if (pos.x == actor.position.x and pos.y == actor.position.y) or is_square_open(pos, battlefield, combatants):
            results.append(pos)
    return results


def distance_in_feet(a: Position, b: Position) -> int:
    return manhattan_distance(a, b) * 5


def attack_in_range(attacker: Combatant, target: Combatant, range_ft: int) -> bool:
    return distance_in_feet(attacker.position, target.position) <= range_ft


def spell_targets_in_radius(center: Position, radius_ft: int, combatants: List[Combatant], enemy_side: str) -> List[Combatant]:
    result: List[Combatant] = []
    for c in combatants:
        if not c.is_alive or c.side != enemy_side:
            continue
        if distance_in_feet(center, c.position) <= radius_ft:
            result.append(c)
    return result
