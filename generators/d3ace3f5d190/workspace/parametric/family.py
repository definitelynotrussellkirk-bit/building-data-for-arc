"""Matched-input axis-selection family for ``d3ace3f5d190``.

Step A locates the unique color-8 corner anchor.  For the alternate setting,
an anchor on a main-diagonal corner selects the main diagonal, while an anchor
on an anti-diagonal corner selects the anti diagonal.  The episode-fixed
default ignores that intermediate and always uses the canonical main diagonal.
Step B applies the same reflected-nonzero-precedence rule through the selected
axis.  Every authored input contains conflicting pairs for both axes so the
replacement semantics, rather than blank-only copying, are observable.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "d3ace3f5d190"
SETTINGS = ("main", "anchor_selected")
DEFAULT = "main"
RIVALS = ("opposite_rule", "always_anti", "copy_blank_only", "move_only")

DEMO_SIZES = (8, 9, 12, 16, 22, 28)
QUERY_SIZES = (11, 18, 24, 30)
COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

_TASK_HOME = Path(__file__).resolve().parents[2]
_name = "_generator_d3a_" + hashlib.sha256(str(_TASK_HOME).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _TASK_HOME / "generator.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load task generator.py")
generator = importlib.util.module_from_spec(_spec)
sys.modules[_name] = generator
_spec.loader.exec_module(generator)


def integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def setting(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("axis_rule must be main or anchor_selected")
    return value


def _partner(n: int, cell: tuple[int, int], axis: str) -> tuple[int, int]:
    r, c = cell
    return (c, r) if axis == "main" else (n - 1 - c, n - 1 - r)


def _corner_anchor(grid: object) -> tuple[int, int]:
    errors = generator._shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    n = len(grid)  # type: ignore[arg-type]
    corners = ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1))
    anchors = [(r, c) for r, c in corners if grid[r][c] == 8]  # type: ignore[index]
    all_eights = [(r, c) for r in range(n) for c in range(n) if grid[r][c] == 8]  # type: ignore[index]
    if len(anchors) != 1 or all_eights != anchors:
        raise ValueError("expected exactly one color-8 cell and it must be a corner anchor")
    return anchors[0]


def _axis_conflicts(grid: list[list[int]], axis: str) -> int:
    n = len(grid)
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    count = 0
    for r in range(n):
        for c in range(n):
            other = _partner(n, (r, c), axis)
            if other == (r, c):
                continue
            key = tuple(sorted(((r, c), other)))
            if key in seen:
                continue
            seen.add(key)
            rr, cc = other
            if grid[r][c] and grid[rr][cc] and grid[r][c] != grid[rr][cc]:
                count += 1
    return count


def intermediate(value: object) -> dict[str, Any]:
    anchor = _corner_anchor(value)
    n = len(value)  # type: ignore[arg-type]
    selected = "main" if anchor[0] == anchor[1] else "anti"
    return {
        "height": n,
        "width": n,
        "anchor": list(anchor),
        "unique_corner_anchor": True,
        "selected_axis": selected,
        "main_conflicts": _axis_conflicts(value, "main"),  # type: ignore[arg-type]
        "anti_conflicts": _axis_conflicts(value, "anti"),  # type: ignore[arg-type]
        "nonzero_cells": sum(cell != 0 for row in value for cell in row),  # type: ignore[union-attr]
    }


def solve_axis(value: object, axis: str) -> list[list[int]]:
    if axis not in ("main", "anti"):
        raise ValueError("axis must be main or anti")
    return generator.rule_mirror(value, axis)


def solve(value: object, axis_rule: str) -> list[list[int]]:
    mode = setting(axis_rule)
    axis = "main" if mode == "main" else intermediate(value)["selected_axis"]
    return solve_axis(value, axis)


def _copy_blank_only(value: object, mode: str) -> list[list[int]]:
    axis = "main" if mode == "main" else intermediate(value)["selected_axis"]
    return generator.copy_blank_only_rival(value, axis)


def _move_only(value: object, mode: str) -> list[list[int]]:
    axis = "main" if mode == "main" else intermediate(value)["selected_axis"]
    return generator.move_only_rival(value, axis)


def solve_rival(value: object, axis_rule: str, rival: str) -> list[list[int]]:
    mode = setting(axis_rule)
    if rival not in RIVALS:
        raise ValueError("unknown rival")
    if rival == "opposite_rule":
        return solve(value, "anchor_selected" if mode == "main" else "main")
    if rival == "always_anti":
        return solve_axis(value, "anti")
    if rival == "copy_blank_only":
        return _copy_blank_only(value, mode)
    return _move_only(value, mode)


def _derived_seed(seed: int, split: str, index: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}:axis-v1:{seed}:{split}:{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _orbit_pairs(n: int, axis: str, forbidden: set[tuple[int, int]]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    rows: list[tuple[tuple[int, int], tuple[int, int]]] = []
    corners = {(0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)}
    for r in range(n):
        for c in range(n):
            other = _partner(n, (r, c), axis)
            if other == (r, c):
                continue
            key = tuple(sorted(((r, c), other)))
            if key in seen:
                continue
            seen.add(key)
            if set(key) & (forbidden | corners):
                continue
            rows.append((key[0], key[1]))
    return rows


def _pick_pair(
    n: int,
    axis: str,
    used: set[tuple[int, int]],
    rng: random.Random,
) -> tuple[tuple[int, int], tuple[int, int]]:
    pairs = _orbit_pairs(n, axis, used)
    rng.shuffle(pairs)
    if not pairs:
        raise AssertionError("no free reflected pair")
    return pairs[0]


def _anchor_for(seed: int, split: str, index: int, n: int) -> tuple[int, int]:
    # Every two-demo prefix includes one anti-axis and one main-axis decision.
    wants_anti = index % 2 == 0
    rng = random.Random(_derived_seed(seed, split + ":anchor", index))
    choices = ((0, n - 1), (n - 1, 0)) if wants_anti else ((0, 0), (n - 1, n - 1))
    return choices[rng.randrange(len(choices))]


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    sizes = DEMO_SIZES if split == "train" else QUERY_SIZES
    n = sizes[index]
    rng = random.Random(_derived_seed(seed, split, index))
    grid = [[0 for _ in range(n)] for _ in range(n)]
    anchor = _anchor_for(seed, split, index, n)
    grid[anchor[0]][anchor[1]] = 8
    used = {anchor}

    main_pair = _pick_pair(n, "main", used, rng)
    used.update(main_pair)
    grid[main_pair[0][0]][main_pair[0][1]] = 1
    grid[main_pair[1][0]][main_pair[1][1]] = 2

    anti_pair = _pick_pair(n, "anti", used, rng)
    used.update(anti_pair)
    grid[anti_pair[0][0]][anti_pair[0][1]] = 3
    grid[anti_pair[1][0]][anti_pair[1][1]] = 4

    target_nonzero = max(14, (n * n) // 10)
    candidates = [
        (r, c)
        for r in range(n)
        for c in range(n)
        if (r, c) not in used
    ]
    rng.shuffle(candidates)
    color_offset = rng.randrange(len(COLORS))
    while sum(value != 0 for row in grid for value in row) < target_nonzero:
        if not candidates:
            raise AssertionError("authored scene ran out of cells")
        r, c = candidates.pop()
        grid[r][c] = COLORS[(color_offset + r * 3 + c * 5) % len(COLORS)]

    errors = generator.self_check(grid)
    if errors:
        raise AssertionError(f"authored scene outside repaired base grammar: {errors}")
    info = intermediate(grid)
    if info["main_conflicts"] < 1 or info["anti_conflicts"] < 1:
        raise AssertionError("authored scene lost an axis-conflict witness")
    if solve_axis(grid, "main") == solve_axis(grid, "anti"):
        raise AssertionError("authored scene does not distinguish the two axes")
    return grid


def generate(seed: object, axis_rule: object, demos: object, queries: object) -> dict[str, Any]:
    seed_i = integer(seed, 0, 2**63 - 1, "seed")
    mode = setting(axis_rule)
    demo_count = integer(demos, 2, 6, "demos")
    query_count = integer(queries, 1, 4, "queries")
    train = []
    for index in range(demo_count):
        data = _draw(seed_i, "train", index)
        train.append({"input": data, "output": solve(data, mode)})
    test = []
    for index in range(query_count):
        data = _draw(seed_i, "test", index)
        test.append({"input": data, "output": solve(data, mode)})
    return {"train": train, "test": test, "private_query_bank": copy.deepcopy(test)}
