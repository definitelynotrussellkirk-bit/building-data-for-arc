"""Canonical-profile generator for ARC task b91ae062 / 4ca8a7b38652.

The authoritative rule counts DISTINCT NONZERO colors.  Let that count be n.
For n > 1, every input cell is expanded to an n-by-n block; zero remains a
normal pixel in the enlarged grid but is excluded from the scale count.

Canonical inputs are sparse 3x3 grids containing zero and two to four nonzero
colors.  This sampler keeps that profile while also scheduling zero-free 3x3
examples.  The zero-free examples distinguish the intended rule from the
canonical-only shortcut "count every color, then subtract one".  Five-sample
windows contain redundant zero-present/zero-free and scale-2/scale-4 witnesses,
so any one-pair query rotation still refutes every declared competitor.
"""
from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "4ca8a7b38652"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2e2cb8677499"
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Generate a 3x3 grid with two to four distinct nonzero colors. Count only "
    "those nonzero colors; if the count is n, upscale every input cell to an "
    "n-by-n block. Canonical-profile sparse examples contain zero, while two "
    "scheduled zero-free examples per five-sample lesson disprove the tempting "
    "canonical-only shortcut of always subtracting one from the total color count."
)

INVARIANTS = [
    "every generated input is exactly 3x3, matching every canonical input",
    "the input contains exactly 2..4 distinct nonzero colors",
    "zero, when present, is excluded from the upscale factor",
    "every five-sample window has three zero-present and two zero-free examples",
    "every five-sample window has at least two scale-2 and two scale-4 examples",
    "zero-present frequency profiles cover every canonical input profile",
    "every exact declared override is recoverable from returned pixels",
    "the authoritative output repeats each cell in an n-by-n block",
]

AXES = {
    "color_count": {
        "type": "int",
        "default": "scheduled 2,3,4,2,4",
        "valid": "2..4",
    },
    "zero_present": {
        "type": "bool",
        "default": "scheduled true,false,true,false,true",
        "valid": "true|false",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# The period has duplicate scale-2 and scale-4 witnesses and duplicate
# zero-free witnesses.  Any six consecutive materialized pairs, with any one
# held out as query, leave all decisive contrasts in the five demonstrations.
_SCHEDULE: tuple[tuple[int, bool], ...] = (
    (2, True),
    (3, False),
    (4, True),
    (2, False),
    (4, True),
)

# Template labels: -1 is zero; 0..3 are palette indices.  Zero-present
# variants reproduce all sorted canonical frequency profiles:
# n=2: [1,3,5] or [2,2,5]
# n=3: [1,1,2,5] or [1,2,2,4]
# n=4: [1,1,1,2,4]
_ZERO_TEMPLATES: dict[int, tuple[tuple[int, ...], ...]] = {
    2: (
        (-1, 0, -1, 1, -1, 0, -1, 1, -1),
        (-1, 0, -1, 0, -1, 0, -1, 1, -1),
    ),
    3: (
        (-1, 0, -1, 1, 2, 0, -1, 1, -1),
        (-1, 0, -1, 1, -1, 0, -1, 2, -1),
    ),
    4: (
        (-1, 0, -1, 1, 2, 0, -1, 3, -1),
    ),
}

_ZERO_FREE_TEMPLATES: dict[int, tuple[int, ...]] = {
    2: (0, 0, 1, 0, 1, 1, 0, 1, 0),
    3: (0, 1, 2, 1, 2, 0, 2, 0, 1),
    4: (0, 1, 2, 3, 0, 1, 2, 3, 0),
}

_ALLOWED_PROFILES: dict[tuple[bool, int], set[tuple[int, ...]]] = {
    (True, 2): {(1, 3, 5), (2, 2, 5)},
    (True, 3): {(1, 1, 2, 5), (1, 2, 2, 4)},
    (True, 4): {(1, 1, 1, 2, 4)},
    (False, 2): {(4, 5)},
    (False, 3): {(3, 3, 3)},
    (False, 4): {(2, 2, 2, 3)},
}


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if overrides.get("color_count") is not None and type(overrides["color_count"]) is not int:
        raise ValueError("color_count override must be an integer, not bool/float/string")
    if overrides.get("zero_present") is not None and type(overrides["zero_present"]) is not bool:
        raise ValueError("zero_present override must be a bool")


def _scheduled_profile(seed: int, sample_index: int) -> tuple[int, bool]:
    return _SCHEDULE[(seed + sample_index) % LESSON_SCHEDULE_PERIOD]


def _rotate(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid: list[list[int]], variant: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    if variant >= 4:
        out = [row[::-1] for row in out]
    for _ in range(variant % 4):
        out = _rotate(out)
    return out


def _has_row_col_variation(grid: list[list[int]]) -> bool:
    rows = {tuple(row) for row in grid}
    cols = {tuple(grid[r][c] for r in range(3)) for c in range(3)}
    return len(rows) >= 2 and len(cols) >= 2


def _is_solid_two_by_two_partition(grid: list[list[int]]) -> bool:
    """Reject the two-color 4/5 split whose minority is one solid 2x2 block."""
    if _grid_shape(grid) != (3, 3) or len(_colors(grid)) != 2:
        return False
    for color in _colors(grid):
        cells = {
            (row, col)
            for row in range(3)
            for col in range(3)
            if grid[row][col] == color
        }
        for top in (0, 1):
            for left in (0, 1):
                block = {
                    (row, col)
                    for row in range(top, top + 2)
                    for col in range(left, left + 2)
                }
                if cells == block:
                    return True
    return False


def _layout(labels: tuple[int, ...], *, difficulty: str, rng) -> list[list[int]]:
    base = [list(labels[i : i + 3]) for i in range(0, 9, 3)]
    if difficulty == "hard":
        cells = list(labels)
        for _ in range(64):
            rng.shuffle(cells)
            candidate = [cells[i : i + 3] for i in range(0, 9, 3)]
            if (
                _has_row_col_variation(candidate)
                and not _is_solid_two_by_two_partition(candidate)
            ):
                return [row[:] for row in candidate]
        raise RuntimeError("failed to realize a varied hard 3x3 layout")
    variants = 4 if difficulty == "easy" else 8
    return _transform(base, rng.randrange(variants))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input grid; outputs remain Racket-authoritative."""
    _validate_override_keys(overrides)
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    band = "medium" if difficulty is None else difficulty
    scheduled_n, scheduled_zero = _scheduled_profile(seed, sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides.get("color_count") is None:
        n = ctx.draw_int_strict("color_count", scheduled_n, scheduled_n)
    else:
        n = ctx.draw_int_strict("color_count", 2, 4)

    if overrides.get("zero_present") is None:
        zero_present = ctx.draw_choice("zero_present", (scheduled_zero,))
    else:
        zero_present = ctx.draw_choice("zero_present", (False, True))

    palette = list(ctx.draw_distinct_colors("palette", n=n, exclude={0}))
    ctx.draw_rng("palette_order").shuffle(palette)

    if zero_present:
        templates = _ZERO_TEMPLATES[n]
        labels = ctx.draw_choice("frequency_profile", templates)
    else:
        labels = _ZERO_FREE_TEMPLATES[n]

    label_grid = _layout(labels, difficulty=band, rng=ctx.draw_rng(f"layout_{band}"))
    grid = [
        [0 if label == -1 else palette[label] for label in row]
        for row in label_grid
    ]
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid:
        return None
    if not all(isinstance(row, list) and row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def _colors(grid: list[list[int]]) -> set[int]:
    return {value for row in grid for value in row}


def _nonzero_colors(grid: list[list[int]]) -> set[int]:
    return _colors(grid) - {0}


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover each exact declared axis from returned pixels."""
    shape = _grid_shape(grid)
    if shape is None:
        return {"color_count": -1, "zero_present": False}
    colors = _colors(grid)
    return {
        "color_count": len(colors - {0}),
        "zero_present": 0 in colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical-profile teaching manifold, not the output rule."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a non-empty rectangular list of rows"]
    errors: list[str] = []
    if shape != (3, 3):
        errors.append(f"teaching inputs must be canonical-profile 3x3, got {shape[0]}x{shape[1]}")

    bad = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad:
        errors.append("all cells must be integer ARC colors 0..9")
        return errors

    colors = _colors(grid)
    nonzero_count = len(colors - {0})
    if not 2 <= nonzero_count <= 4:
        errors.append(f"expected 2..4 distinct nonzero colors, got {nonzero_count}")
        return errors

    zero_present = 0 in colors
    counts = Counter(value for row in grid for value in row)
    if zero_present and counts[0] not in {4, 5}:
        errors.append(f"zero must occupy 4 or 5 canonical-profile cells, got {counts[0]}")
    profile = tuple(sorted(counts.values()))
    allowed = _ALLOWED_PROFILES[(zero_present, nonzero_count)]
    if profile not in allowed:
        errors.append(
            f"frequency profile {profile} is outside the declared "
            f"zero_present={zero_present}, color_count={nonzero_count} profiles"
        )
    if shape == (3, 3) and not _has_row_col_variation(grid):
        errors.append("inputs must vary across both rows and columns")
    if shape == (3, 3) and _is_solid_two_by_two_partition(grid):
        errors.append("two-color inputs must not be a solid 2x2 minority partition")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every emitted grid is inside the declared strict teaching manifold."""
    return self_check(grid)


def mutation_fixtures():
    """Small task-linked impostors that a useful distribution check must reject."""
    return [
        ("blank", [[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        ("one_nonzero_color", [[0, 1, 0], [1, 0, 1], [0, 1, 0]]),
        ("zero_free_singleton", [[1, 1, 1], [1, 1, 1], [1, 1, 2]]),
        ("zero_profile_too_dense", [[0, 1, 1], [1, 1, 1], [2, 2, 2]]),
    ]


def _upscale_with_factor(grid: list[list[int]], factor: int) -> list[list[int]]:
    if factor <= 1:
        return copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    return [
        [grid[r // factor][c // factor] for c in range(w * factor)]
        for r in range(h * factor)
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests and semantic rival analysis."""
    return _upscale_with_factor(grid, len(_nonzero_colors(grid)))


def semantic_observables(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    counts = Counter(value for row in grid for value in row)
    n = len(set(counts) - {0})
    return {
        "errors": [],
        "color_count": n,
        "zero_present": 0 in counts,
        "frequency_profile": sorted(counts.values()),
        "nonzero_cells": sum(value != 0 for row in grid for value in row),
        "output_shape": [3 * n, 3 * n],
    }


def _rival_count_all_colors(grid):
    return _upscale_with_factor(grid, len(_colors(grid)))


def _rival_always_subtract_one(grid):
    return _upscale_with_factor(grid, max(1, len(_colors(grid)) - 1))


def _rival_fixed_three(grid):
    return _upscale_with_factor(grid, 3)


def _rival_nonzero_cell_count(grid):
    factor = sum(value != 0 for row in grid for value in row)
    return _upscale_with_factor(grid, factor)


def _rival_max_nonzero_frequency(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    return _upscale_with_factor(grid, max(counts.values()))


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "count_all_colors": _rival_count_all_colors,
    "always_subtract_one": _rival_always_subtract_one,
    "fixed_three": _rival_fixed_three,
    "scale_by_nonzero_cell_count": _rival_nonzero_cell_count,
    "scale_by_max_nonzero_frequency": _rival_max_nonzero_frequency,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every canonical input contains zero, so this rival fits all public pairs.
    "always_subtract_one": _rival_always_subtract_one,
}


def _has_scale(expected: int):
    return lambda grid: len(_nonzero_colors(grid)) == expected


SEMANTIC_WITNESSES = {
    "scale_two": _has_scale(2),
    "scale_four": _has_scale(4),
    "zero_is_excluded": lambda grid: 0 in _colors(grid),
    "zero_free_same_rule": lambda grid: 0 not in _colors(grid),
    "nonzero_cells_differ_from_factor": lambda grid: (
        sum(value != 0 for row in grid for value in row)
        != len(_nonzero_colors(grid))
    ),
    "max_frequency_differs_from_factor": lambda grid: (
        max(Counter(value for row in grid for value in row if value != 0).values())
        != len(_nonzero_colors(grid))
    ),
}
WITNESS_RIVALS = {
    "scale_two": ["fixed_three"],
    "scale_four": ["fixed_three"],
    "zero_is_excluded": ["count_all_colors"],
    "zero_free_same_rule": ["always_subtract_one"],
    "nonzero_cells_differ_from_factor": ["scale_by_nonzero_cell_count"],
    "max_frequency_differs_from_factor": ["scale_by_max_nonzero_frequency"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require correct labels and decisive evidence in every materialized lesson."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    zero_present = False
    zero_free = False
    scales: set[int] = set()
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} disagrees with nonzero-color-count upscaling")
        colors = _colors(pair["input"])
        zero_present |= 0 in colors
        zero_free |= 0 not in colors
        scales.add(len(colors - {0}))
        valid_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is unlawful: " + "; ".join(query_errors))
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query disagrees with nonzero-color-count upscaling")

    if not zero_present:
        reasons.append("demonstrations need a zero-present example")
    if not zero_free:
        reasons.append("demonstrations need a zero-free example")
    if 2 not in scales or 4 not in scales:
        reasons.append("demonstrations need both scale-2 and scale-4 examples")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"]
            for pair in valid_demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
