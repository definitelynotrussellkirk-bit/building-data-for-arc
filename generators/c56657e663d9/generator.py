"""Generator for ``echo_cells_across_the_main_diagonal``.

For each coordinate ``(r, c)``, the selected Racket rule reads the transposed
cell ``(c, r)``.  A nonzero transposed value overwrites the current value;
otherwise the current value is preserved.  Therefore each off-diagonal pair
has three decisive behaviours:

* a one-sided cell is copied to the empty partner;
* two different nonzero values swap positions;
* two equal nonzero values remain unchanged.

Normal draws include upper-only, lower-only, and different-color conflict
pairs in every instance.  That prevents the historical shortcut where all
sources lived above the diagonal and a simple upper-triangle mirror matched
all generated data.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c56657e663d9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "38eb4ea53ac4"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a square background-0 grid, inspect every cell together with its main-"
    "diagonal transpose partner. If the transposed cell is nonzero, write that "
    "value here; otherwise preserve the current value. One-sided cells are "
    "therefore copied to both positions, while different nonzero values across "
    "the diagonal swap positions."
)

INVARIANTS = [
    "background is 0 and every input is a square ARC grid",
    "normal draws contain upper-only and lower-only off-diagonal cells",
    "normal draws contain at least one different-color occupied transpose pair",
    "the Racket oracle, not the Python mirror, is the output authority",
]

AXES = {
    "size": {
        "type": "int",
        "default": "difficulty-weighted keyed draw",
        "valid": "6..10",
    },
    "conflict_pairs": {
        "type": "int",
        "default": "difficulty-weighted keyed draw",
        "valid": "1..2",
    },
    "one_sided_pairs": {
        "type": "int",
        "default": "difficulty-weighted keyed draw",
        "valid": "2..3",
    },
    "diagonal_cells": {
        "type": "int",
        "default": "difficulty-weighted keyed draw",
        "valid": "0..1",
    },
    "palette_size": {
        "type": "int",
        "default": "keyed draw",
        "valid": "2..4",
    },
}

# Declaring the empty list switches the override checker to the strict policy:
# every Cartesian boundary combination is intentionally supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_SIZE_OPTIONS = {
    None: (6, 6, 7, 7, 8, 8, 9, 10),
    "easy": (6, 6, 6, 7, 7, 8, 9, 10),
    "medium": (6, 7, 7, 8, 8, 9, 9, 10),
    "hard": (6, 7, 8, 8, 8, 9, 9, 10),
}
_PALETTE_OPTIONS = {
    None: (2, 3, 3, 4),
    "easy": (2, 2, 3, 3, 4),
    "medium": (2, 3, 3, 4),
    "hard": (2, 3, 4, 4),
}


def _validate_call(difficulty: object, overrides: dict[str, object]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name in (
        "size",
        "conflict_pairs",
        "one_sided_pairs",
        "diagonal_cells",
        "palette_size",
    ):
        value = overrides.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError(f"{name} must be an integer")


def _one_sided_counts(total: int, extra_side: str) -> tuple[int, int]:
    """Every draw covers both directions; a third pair varies the emphasis."""
    if total == 2:
        return 1, 1
    if total == 3 and extra_side == "upper":
        return 2, 1
    if total == 3 and extra_side == "lower":
        return 1, 2
    raise ValueError("one_sided_pairs must be 2..3")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, branch-complete input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    size = ctx.draw_choice("size", _SIZE_OPTIONS[difficulty])
    conflict_pairs = ctx.draw_int_diff("conflict_pairs", 1, 2)
    one_sided_pairs = ctx.draw_int_diff("one_sided_pairs", 2, 3)
    extra_side = ctx.draw_choice("extra_side", ("upper", "lower"))
    diagonal_cells = ctx.draw_int_diff("diagonal_cells", 0, 1)
    palette_size = ctx.draw_choice("palette_size", _PALETTE_OPTIONS[difficulty])
    colors = ctx.draw_distinct_colors("colors", n=palette_size, exclude={0})

    upper_count, lower_count = _one_sided_counts(one_sided_pairs, extra_side)
    pairs = [(r, c) for r in range(size) for c in range(r + 1, size)]
    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(pairs)
    needed = conflict_pairs + one_sided_pairs
    if needed > len(pairs):
        raise ValueError("requested pair counts do not fit the selected size")

    conflict_positions = pairs[:conflict_pairs]
    one_sided_positions = pairs[conflict_pairs:needed]
    layout_rng.shuffle(one_sided_positions)
    upper_positions = one_sided_positions[:upper_count]
    lower_positions = one_sided_positions[upper_count:upper_count + lower_count]

    diagonals = list(range(size))
    layout_rng.shuffle(diagonals)
    diagonal_positions = diagonals[:diagonal_cells]

    grid = full_grid(size, size, 0)
    color_index = 0

    # A conflict always uses two different colors. This branch is the decisive
    # counterexample to "fill only blank transpose partners" and to either
    # fixed-side precedence shortcut.
    for r, c in conflict_positions:
        upper_color = colors[color_index % palette_size]
        lower_color = colors[(color_index + 1) % palette_size]
        grid[r][c] = upper_color
        grid[c][r] = lower_color
        color_index += 2

    for r, c in upper_positions:
        grid[r][c] = colors[color_index % palette_size]
        color_index += 1
    for r, c in lower_positions:
        grid[c][r] = colors[color_index % palette_size]
        color_index += 1
    for d in diagonal_positions:
        grid[d][d] = colors[color_index % palette_size]
        color_index += 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator invariant failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "size": size,
        "conflict_pairs": conflict_pairs,
        "one_sided_pairs": one_sided_pairs,
        "diagonal_cells": diagonal_cells,
        "palette_size": palette_size,
    }
    if observed != requested:
        raise AssertionError(f"axis observation mismatch: {requested=} {observed=}")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _pair_profile(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> dict[str, int]:
    size = len(grid)
    profile = {
        "upper_only": 0,
        "lower_only": 0,
        "conflict_diff": 0,
        "conflict_same": 0,
        "diagonal": 0,
        "occupied_pairs": 0,
    }
    for r in range(size):
        if grid[r][r] != 0:
            profile["diagonal"] += 1
        for c in range(r + 1, size):
            upper, lower = grid[r][c], grid[c][r]
            if upper == 0 and lower == 0:
                continue
            profile["occupied_pairs"] += 1
            if upper != 0 and lower == 0:
                profile["upper_only"] += 1
            elif upper == 0 and lower != 0:
                profile["lower_only"] += 1
            elif upper == lower:
                profile["conflict_same"] += 1
            else:
                profile["conflict_diff"] += 1
    return profile


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical sparse square grammar and reject rule-hiding scenes."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if height != width:
        return [f"expected square grid, found {height}x{width}"]
    if not 4 <= height <= 14:
        errors.append(f"square size must be in 4..14, found {height}")

    nonzero = sum(value != 0 for row in grid for value in row)
    if nonzero == 0:
        errors.append("no nonzero cells found")
    if nonzero > min(12, max(6, height * height // 3)):
        errors.append(f"scene is too dense for the canonical sparse-cell grammar ({nonzero} cells)")
    if _is_axis_aligned_line_scene(grid):
        errors.append("all nonzero cells form one horizontal/vertical line outside the sparse-cell grammar")

    profile = _pair_profile(grid)
    if profile["occupied_pairs"] == 0:
        errors.append("all nonzero cells are diagonal; the transpose branch is hidden")
    if profile["upper_only"] + profile["lower_only"] == 0:
        errors.append("no one-sided transpose pair; copy-to-empty behavior is hidden")
    if (
        profile["upper_only"]
        + profile["lower_only"]
        + profile["conflict_diff"]
        == 0
    ):
        errors.append("input is already transpose-symmetric; the rule is a no-op")
    return errors


def _is_axis_aligned_line_scene(grid) -> bool:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(cells) < 3:
        return False
    return len({r for r, _ in cells}) == 1 or len({c for _, c in cells}) == 1


def strict_canonical_like(grid) -> list[str]:
    """Normal draws and every canonical input live inside this exact grammar."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python spelling of the selected Racket rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if len(grid) != len(grid[0]):
        raise ValueError("rule requires a square grid")
    size = len(grid)
    return [
        [grid[c][r] if grid[c][r] != 0 else grid[r][c] for c in range(size)]
        for r in range(size)
    ]


def _identity(grid):
    return deepcopy(grid)


def _transpose_only(grid):
    size = len(grid)
    return [[grid[c][r] for c in range(size)] for r in range(size)]


def _fill_blanks_only(grid):
    """Copy one-sided cells but preserve both values of occupied conflicts."""
    out = deepcopy(grid)
    size = len(grid)
    for r in range(size):
        for c in range(r + 1, size):
            upper, lower = grid[r][c], grid[c][r]
            if upper != 0 and lower == 0:
                out[c][r] = upper
            elif upper == 0 and lower != 0:
                out[r][c] = lower
    return out


def _upper_precedence(grid):
    out = deepcopy(grid)
    size = len(grid)
    for r in range(size):
        for c in range(r + 1, size):
            upper, lower = grid[r][c], grid[c][r]
            value = upper if upper != 0 else lower
            out[r][c] = value
            out[c][r] = value
    return out


def _lower_precedence(grid):
    out = deepcopy(grid)
    size = len(grid)
    for r in range(size):
        for c in range(r + 1, size):
            upper, lower = grid[r][c], grid[c][r]
            value = lower if lower != 0 else upper
            out[r][c] = value
            out[c][r] = value
    return out


SEMANTIC_RIVALS = {
    "identity": _identity,
    "transpose_only": _transpose_only,
    "fill_blanks_only": _fill_blanks_only,
    "upper_precedence": _upper_precedence,
    "lower_precedence": _lower_precedence,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_upper_only(grid) -> bool:
    return not self_check(grid) and _pair_profile(grid)["upper_only"] > 0


def _witness_lower_only(grid) -> bool:
    return not self_check(grid) and _pair_profile(grid)["lower_only"] > 0


def _witness_conflict_swap(grid) -> bool:
    return not self_check(grid) and _pair_profile(grid)["conflict_diff"] > 0


SEMANTIC_WITNESSES = {
    "upper_only_copy": _witness_upper_only,
    "lower_only_copy": _witness_lower_only,
    "different_color_conflict_swap": _witness_conflict_swap,
}
WITNESS_RIVALS = {
    "upper_only_copy": ["identity", "transpose_only"],
    "lower_only_copy": ["identity", "transpose_only"],
    "different_color_conflict_swap": [
        "fill_blanks_only",
        "upper_precedence",
        "lower_precedence",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that expose all decisive off-diagonal branches."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    seen = {"upper_only": False, "lower_only": False, "conflict_diff": False}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_errors = self_check(demo["input"])
        if input_errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not match transpose-overlay semantics")
        profile = _pair_profile(demo["input"])
        for branch in seen:
            seen[branch] = seen[branch] or profile[branch] > 0

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the teaching grammar")
    else:
        query_profile = _pair_profile(query["input"])
        if not all(query_profile[branch] > 0 for branch in seen):
            reasons.append("query does not contain every decisive off-diagonal branch")

    missing = [name for name, present in seen.items() if not present]
    if missing:
        reasons.append("demonstrations hide branch(es): " + ", ".join(missing))
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact axis from the returned grid itself."""
    if _grid_errors(grid) or len(grid) != len(grid[0]):
        return {}
    profile = _pair_profile(grid)
    upper, lower = profile["upper_only"], profile["lower_only"]
    return {
        "size": len(grid),
        "conflict_pairs": profile["conflict_diff"],
        "one_sided_pairs": upper + lower,
        "diagonal_cells": profile["diagonal"],
        "palette_size": len({value for row in grid for value in row if value != 0}),
    }


def mutation_fixtures():
    """Task-local malformed scenes that the structural checker must reject."""
    nonsquare = full_grid(5, 6, 0)
    nonsquare[1][4] = 3

    all_diagonal = full_grid(6, 6, 0)
    all_diagonal[1][1] = 2
    all_diagonal[4][4] = 7

    already_symmetric = full_grid(6, 6, 0)
    already_symmetric[1][4] = 3
    already_symmetric[4][1] = 3

    conflict_only = full_grid(6, 6, 0)
    conflict_only[1][4] = 3
    conflict_only[4][1] = 7

    empty = full_grid(6, 6, 0)
    return [
        ("non_square", nonsquare),
        ("all_on_diagonal", all_diagonal),
        ("already_symmetric", already_symmetric),
        ("conflict_without_copy_branch", conflict_only),
        ("empty_grid", empty),
    ]
