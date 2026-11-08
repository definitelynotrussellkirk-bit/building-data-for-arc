"""Independent review oracle and probes for f8b9516df05e."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any

TASK_ID = "f8b9516df05e"
ROOT = Path(__file__).resolve().parents[3]


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_facts(row: list[int]) -> tuple[int, int, int] | None:
    emitters = [c for c, value in enumerate(row) if value not in (0, 8)]
    if not emitters:
        return None
    emit = emitters[0]
    blockers = [c for c in range(emit + 1, len(row)) if row[c] == 8]
    if not blockers:
        return None
    return emit, blockers[0], row[emit]


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Direct Python mirror of the selected Racket authority."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        facts = row_facts(row)
        if facts is None:
            continue
        emit, blocker, color = facts
        for c in range(emit + 1, blocker):
            out[r][c] = color
    return out


def skip_unit_gap_rival(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: ignores a ray with exactly one empty cell."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        facts = row_facts(row)
        if facts is None:
            continue
        emit, blocker, color = facts
        if blocker - emit - 1 < 2:
            continue
        for c in range(emit + 1, blocker):
            out[r][c] = color
    return out


def ignore_blocker_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: continue the ray through trailing background."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        facts = row_facts(row)
        if facts is None:
            continue
        emit, _blocker, color = facts
        for c in range(emit + 1, len(row)):
            if out[r][c] == 0:
                out[r][c] = color
    return out


def observed(grid: list[list[int]]) -> dict[str, int]:
    rays = 0
    post = 0
    for row in grid:
        facts = row_facts(row)
        if facts is None:
            continue
        rays += 1
        _emit, blocker, _color = facts
        post += sum(value != 0 for value in row[blocker + 1 :])
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rays": rays,
        "post_blocker_cells": post,
    }


def teaching_errors(grid: list[list[int]]) -> list[str]:
    errors: list[str] = []
    facts = [row_facts(row) for row in grid]
    active = [item for item in facts if item is not None]
    if not any(blocker - emit == 2 for emit, blocker, _ in active):
        errors.append("missing a one-cell ray that refutes the canonical shortcut")
    if not any(any(value == 0 for value in grid[r][blocker + 1 :])
               for r, item in enumerate(facts) if item is not None
               for _emit, blocker, _color in (item,)):
        errors.append("missing trailing background that proves the blocker stops the ray")
    official = rule_output(grid)
    if skip_unit_gap_rival(grid) == official:
        errors.append("unit-gap shortcut survives")
    if ignore_blocker_rival(grid) == official:
        errors.append("ignore-blocker rival survives")
    return errors


def malformed_grids() -> tuple[Any, ...]:
    return (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0, 8], [0, 0, 0]],
        [[10, 0, 8]],
        [[8, 0, 0]],
        [[3, 0, 0]],
    )
