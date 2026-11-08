"""Independent review oracle and semantic probes for 26dbe76edccd.

This module deliberately does not import implementation helpers from generator.py.
It is retained so future reviewers can reproduce the rule and override claims from
one small, portable file.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

TASK_ID = "26dbe76edccd"
BLOCKER = 5
SEED_COLORS = frozenset({1, 2, 3, 4, 6, 7, 8, 9})


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Literal Python reading of the selected rule: every seed casts right."""
    out = deepcopy(grid)
    if not grid:
        return out
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, BLOCKER):
                continue
            cc = c + 1
            while cc < width and row[cc] != BLOCKER:
                out[r][cc] = value
                cc += 1
    return out


def row_facts(row: list[int]) -> tuple[int, int | None, int] | None:
    seeds = [c for c, value in enumerate(row) if value not in (0, BLOCKER)]
    if len(seeds) != 1:
        return None
    emitter = seeds[0]
    right = [c for c in range(emitter + 1, len(row)) if row[c] == BLOCKER]
    return emitter, (right[0] if right else None), row[emitter]


def observed(grid: list[list[int]]) -> dict[str, int]:
    active = []
    terminating = 0
    for row in grid:
        facts = row_facts(row)
        if facts is None:
            continue
        active.append(facts)
        if facts[1] is not None:
            terminating += 1
    blocker_count = sum(value == BLOCKER for row in grid for value in row)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rays": len(active),
        "extra_blockers": blocker_count - terminating,
    }


def skip_unit_gap_rival(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        facts = row_facts(row)
        if facts is None:
            continue
        emitter, blocker, color = facts
        stop = len(row) if blocker is None else blocker
        if stop - emitter - 1 == 1:
            continue
        for c in range(emitter + 1, stop):
            out[r][c] = color
    return out


def ignore_blocker_rival(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        facts = row_facts(row)
        if facts is None:
            continue
        emitter, _blocker, color = facts
        for c in range(emitter + 1, len(row)):
            if out[r][c] == 0:
                out[r][c] = color
    return out


def last_blocker_rival(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        facts = row_facts(row)
        if facts is None:
            continue
        emitter, first, color = facts
        if first is None:
            stop = len(row)
        else:
            stop = max(c for c in range(emitter + 1, len(row)) if row[c] == BLOCKER)
        for c in range(emitter + 1, stop):
            if out[r][c] == 0:
                out[r][c] = color
    return out


def require_blocker_rival(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        facts = row_facts(row)
        if facts is None:
            continue
        emitter, blocker, color = facts
        if blocker is None:
            continue
        for c in range(emitter + 1, blocker):
            out[r][c] = color
    return out


RIVALS = {
    "skip_unit_gap": skip_unit_gap_rival,
    "ignore_blocker": ignore_blocker_rival,
    "last_blocker": last_blocker_rival,
    "require_blocker": require_blocker_rival,
}


def teaching_errors(grid: list[list[int]]) -> list[str]:
    official = rule_output(grid)
    return [name for name, rival in RIVALS.items() if rival(grid) == official]


def malformed_grids() -> tuple[Any, ...]:
    return (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0, 5, 0, 0, 0, 0] for _ in range(5)],
        [[10, 0, 5, 0, 0, 0, 0] for _ in range(5)],
        [[0] * 7 for _ in range(5)],
    )
