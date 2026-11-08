"""Semantic generator for ARC task aa300dc3 / 2e9bbcd910a7.

The official inputs are 10x10 boards with a solid gray border and a dense,
4-connected black interior interrupted by gray blockers.  The Racket rule
finds maximal black runs along the two downward diagonal directions, ranks
runs by length and then by its explicit start-position tie-break, and paints
the winning run cyan.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "2e9bbcd910a7"
TASK_ID = "2e9bbcd910a7"
VERSION = "4.0.0"
RULE_HASH = "88395fd9c397"

SUMMARY = (
    "On a 10x10 grid with a solid gray-5 border, the interior is a dense, "
    "single 4-connected region of black-0 cells with gray-5 blockers. Enumerate "
    "every maximal black run in the down-right and down-left directions. Rank "
    "runs by length; ties prefer the smaller start row, then for down-left the "
    "larger start column and for down-right the smaller start column. Recolor "
    "exactly the winning run cyan-8 and preserve every other cell."
)

INVARIANTS = [
    "the input is exactly 10x10 and uses only colors 0 and 5",
    "the outer border is entirely gray 5",
    "the black interior contains 39..48 cells and is one 4-connected component",
    "the selected diagonal run has length 6..8 and at least one distractor run has length >=5",
    "both diagonal directions, unique winners, near ties, and exact-length ties occur in the curriculum",
    "the input contains no cyan 8; the rule alone writes cyan on the selected run",
]

SCENE_FAMILIES = (
    "unique_se",
    "unique_sw",
    "near_tie_se",
    "near_tie_sw",
    "tie_se",
    "tie_sw",
)

AXES = {
    "scene_family": {
        "type": "str",
        "default": "keyed uniform over six semantic families",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": (
            "Controls winner direction and whether the strongest distractor is "
            "shorter by at least two, shorter by one, or tied and resolved by "
            "the canonical start-position score."
        ),
    }
}

# Paths are tuples of (row, col), all within the 8x8 interior.
def _path(start: tuple[int, int], direction: tuple[int, int], length: int):
    return tuple(
        (start[0] + index * direction[0], start[1] + index * direction[1])
        for index in range(length)
    )


_SE8 = _path((1, 1), (1, 1), 8)
_SW8 = _path((1, 8), (1, -1), 8)
_SE7_LEFT = _path((1, 1), (1, 1), 7)
_SE7_RIGHT = _path((1, 2), (1, 1), 7)
_SW7_RIGHT = _path((1, 8), (1, -1), 7)
_SW7_LEFT = _path((1, 7), (1, -1), 7)
_SE6_OFFSET = _path((1, 3), (1, 1), 6)
_SW5_OFFSET = _path((1, 7), (1, -1), 5)
_SW7_OFFSET = _path((1, 7), (1, -1), 7)
_SE6_LEFT = _path((1, 1), (1, 1), 6)

_FAMILY_VARIANTS = {
    "unique_se": ({
        "protected": (_SE8,),
        "winner": _SE8,
        "max_length": 8,
        "tie": False,
        "near_tie": False,
    },),
    "unique_sw": ({
        "protected": (_SW8,),
        "winner": _SW8,
        "max_length": 8,
        "tie": False,
        "near_tie": False,
    },),
    "near_tie_se": ({
        "protected": (_SE8, _SW7_RIGHT),
        "winner": _SE8,
        "max_length": 8,
        "tie": False,
        "near_tie": True,
    }, {
        "protected": (_SE6_OFFSET, _SW5_OFFSET),
        "winner": _SE6_OFFSET,
        "max_length": 6,
        "tie": False,
        "near_tie": True,
    }),
    "near_tie_sw": ({
        "protected": (_SW8, _SE7_LEFT),
        "winner": _SW8,
        "max_length": 8,
        "tie": False,
        "near_tie": True,
    }, {
        "protected": (_SW7_OFFSET, _SE6_LEFT),
        "winner": _SW7_OFFSET,
        "max_length": 7,
        "tie": False,
        "near_tie": True,
    }),
    "tie_se": ({
        "protected": (_SE7_LEFT, _SE7_RIGHT),
        "winner": _SE7_LEFT,
        "max_length": 7,
        "tie": True,
        "near_tie": False,
    },),
    "tie_sw": ({
        "protected": (_SW7_RIGHT, _SW7_LEFT),
        "winner": _SW7_RIGHT,
        "max_length": 7,
        "tie": True,
        "near_tie": False,
    },),
}


def _valid_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["input must contain rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["input must contain columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["every cell must be an ARC color integer from 0 through 9"]
    return []


def _diagonal_runs(grid):
    """Return maximal zero runs in the same two directions as the Racket rule."""
    height, width = len(grid), len(grid[0])
    runs = []
    for dr, dc, name in ((1, 1, "se"), (1, -1, "sw")):
        for row in range(height):
            for col in range(width):
                if grid[row][col] != 0:
                    continue
                prev_row, prev_col = row - dr, col - dc
                if (
                    0 <= prev_row < height
                    and 0 <= prev_col < width
                    and grid[prev_row][prev_col] == 0
                ):
                    continue
                cells = []
                cursor_row, cursor_col = row, col
                while (
                    0 <= cursor_row < height
                    and 0 <= cursor_col < width
                    and grid[cursor_row][cursor_col] == 0
                ):
                    cells.append((cursor_row, cursor_col))
                    cursor_row += dr
                    cursor_col += dc
                runs.append(
                    {
                        "cells": tuple(cells),
                        "direction": name,
                        "delta": (dr, dc),
                        "start": (row, col),
                    }
                )
    return runs


def _score(run, width: int) -> int:
    row, col = run["start"]
    dc = run["delta"][1]
    return (
        len(run["cells"]) * 10000
        - row * 100
        + (col if dc == -1 else width - col)
    )


def _ranked_runs(grid):
    width = len(grid[0])
    return sorted(_diagonal_runs(grid), key=lambda run: _score(run, width), reverse=True)


def rule_mirror(grid):
    """Input-pure Python mirror used only for tests; Racket remains authority."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    runs = _ranked_runs(grid)
    if not runs:
        raise ValueError("the rule requires at least one black cell")
    output = [list(row) for row in grid]
    for row, col in runs[0]["cells"]:
        output[row][col] = 8
    return output


def _zero_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    }
    components = []
    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(component)
    return components


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if (height, width) != (10, 10):
        errors.append("calibrated longest-diagonal scenes must be exactly 10x10")
    palette = {value for row in grid for value in row}
    if palette != {0, 5}:
        errors.append(f"input palette must be exactly {{0, 5}}, found {sorted(palette)}")
    border_ok = (
        height == 10
        and width == 10
        and all(grid[0][col] == 5 and grid[-1][col] == 5 for col in range(width))
        and all(grid[row][0] == 5 and grid[row][-1] == 5 for row in range(height))
    )
    if not border_ok:
        errors.append("the complete outer border must be gray 5")
    zero_count = sum(value == 0 for row in grid for value in row)
    if not 39 <= zero_count <= 48:
        errors.append(f"black-cell count must be in canonical range 39..48, found {zero_count}")
    components = _zero_components(grid) if height and width else []
    if len(components) != 1:
        errors.append(f"black cells must form one 4-connected component, found {len(components)}")
    ranked = _ranked_runs(grid) if zero_count else []
    lengths = [len(run["cells"]) for run in ranked]
    winner_length = lengths[0] if lengths else 0
    second_length = lengths[1] if len(lengths) > 1 else 0
    if not 6 <= winner_length <= 8:
        errors.append(f"winning diagonal length must be 6..8, found {winner_length}")
    if second_length < 5:
        errors.append(f"at least one distractor diagonal must have length >=5, found {second_length}")
    output = None
    if ranked:
        output = [list(row) for row in grid]
        for row, col in ranked[0]["cells"]:
            output[row][col] = 8
    max_length = winner_length
    max_runs = [run for run in ranked if len(run["cells"]) == max_length]
    facts = {
        "height": height,
        "width": width,
        "palette": palette,
        "border_ok": border_ok,
        "zero_count": zero_count,
        "zero_component_count": len(components),
        "winner_length": winner_length,
        "winner_direction": ranked[0]["direction"] if ranked else None,
        "winner_start": ranked[0]["start"] if ranked else None,
        "second_length": second_length,
        "max_run_count": len(max_runs),
        "long_run_count": sum(length >= 5 for length in lengths),
        "score_gap": (
            _score(ranked[0], width) - _score(ranked[1], width)
            if len(ranked) > 1 else None
        ),
    }
    return {"errors": errors, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the canonical dense-board teaching grammar."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, object]:
    """No exact numeric axes are declared; expose the semantic family anyway."""
    facts = _analysis(grid)["facts"]
    if not facts:
        return {}
    direction = facts["winner_direction"]
    if facts["max_run_count"] >= 2:
        family = f"tie_{direction}"
    elif facts["second_length"] == facts["winner_length"] - 1:
        family = f"near_tie_{direction}"
    else:
        family = f"unique_{direction}"
    return {"scene_family": family}


def _forced_blockers(paths: Iterable[tuple[tuple[int, int], ...]]):
    blockers = set()
    for cells in paths:
        if len(cells) < 2:
            continue
        dr = cells[1][0] - cells[0][0]
        dc = cells[1][1] - cells[0][1]
        before = (cells[0][0] - dr, cells[0][1] - dc)
        after = (cells[-1][0] + dr, cells[-1][1] + dc)
        for row, col in (before, after):
            if 1 <= row <= 8 and 1 <= col <= 8:
                blockers.add((row, col))
    return blockers


def _family_matches(grid, family: str) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    facts = analysis["facts"]
    if facts["winner_direction"] != family[-2:]:
        return False
    if family.startswith("tie_"):
        return facts["max_run_count"] >= 2 and facts["second_length"] == facts["winner_length"]
    if family.startswith("near_tie_"):
        return facts["max_run_count"] == 1 and facts["second_length"] == facts["winner_length"] - 1
    return facts["max_run_count"] == 1 and facts["second_length"] <= facts["winner_length"] - 2


def _variant_matches(grid, family: str, spec: dict[str, object]) -> bool:
    if not _family_matches(grid, family):
        return False
    ranked = _ranked_runs(grid)
    return (
        ranked[0]["cells"] == spec["winner"]
        and len(ranked[0]["cells"]) == spec["max_length"]
    )


def _draw_scene(family: str, difficulty: str | None, rng):
    variants = _FAMILY_VARIANTS[family]
    spec = rng.choice(variants)
    protected = set().union(*map(set, spec["protected"]))
    forced = _forced_blockers(spec["protected"])
    if forced & protected:
        raise AssertionError("family path terminators overlap protected cells")
    zero_ranges = {
        "easy": (46, 48),
        "medium": (42, 46),
        "hard": (39, 43),
    }
    lo, hi = zero_ranges.get(difficulty, (39, 48))
    interior = {(row, col) for row in range(1, 9) for col in range(1, 9)}
    available = sorted(interior - protected - forced)
    for _ in range(2500):
        zero_target = rng.randint(lo, hi)
        blocker_target = 64 - zero_target
        if blocker_target < len(forced):
            continue
        extras_needed = blocker_target - len(forced)
        if extras_needed > len(available):
            continue
        blockers = forced | set(rng.sample(available, extras_needed))
        grid = [[5] * 10 for _ in range(10)]
        for row, col in interior - blockers:
            grid[row][col] = 0
        if _variant_matches(grid, family, spec):
            return grid
    raise RuntimeError(f"could not construct semantic family {family!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice("scene_family", SCENE_FAMILIES)
    rng = ctx.draw_rng("blocker_layout")
    return _draw_scene(family, difficulty, rng)
