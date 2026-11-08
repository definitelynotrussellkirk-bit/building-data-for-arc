"""Generator for ARC task 72207abc.

The input is a 3-row strip.  Row 1 carries a short sequence of distinct seed
colors at the first triangular-number columns (0, 1, and optionally 3); rows 0
and 2 are blank.  The rule cycles that left-to-right seed sequence across all
triangular-number columns that fit in the strip.

The canonical task has only two meaningful structural branches: a 2-color or
3-color cycle, each shown on width 19 or 29.  The generator schedules all four
profiles in every four consecutive sample indices so a materialized lesson
cannot accidentally hide either cycle length or either output extent.
"""
from __future__ import annotations

import copy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8cbd834f4187"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4db26130eaff"

SUMMARY = (
    "A 3xW strip (W is 19 or 29) has all-zero outer rows. Row 1 contains "
    "2 or 3 distinct seed colors at the first triangular columns: [0,1] or "
    "[0,1,3]. Read those colors left-to-right as a sequence. For k=0,1,..., "
    "paint row 1, column k(k+1)/2 with seed[k mod n] while that column fits. "
    "All non-triangular cells remain unchanged (and are zero in lawful inputs)."
)

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is exactly 3 rows by 19 or 29 columns",
    "rows 0 and 2 are entirely color 0",
    "row 1 has exactly 2 or 3 nonzero seed cells",
    "seed cells occupy exactly the first n triangular columns [0,1] or [0,1,3]",
    "seed colors are distinct, so the cycle length and order are visible",
    "every four consecutive sample indices cover both widths and both cycle lengths",
    "every five consecutive sample indices include a descending color order",
]

# Keep the override surface deliberately small and exact.  Color choice and
# ascending/descending order are keyed local variation, not caller controls.
AXES = {
    "grid_w": {
        "type": "int",
        "default": "four-profile sample_index schedule",
        "valid": "19|29",
    },
    "n_seed_cells": {
        "type": "int",
        "default": "four-profile sample_index schedule",
        "valid": "2..3",
    },
}

_TRIANGULAR_COLUMNS = (0, 1, 3, 6, 10, 15, 21, 28)
_PROFILE_CYCLE = ((19, 2), (29, 3), (19, 3), (29, 2))
_DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")


def _scheduled_profile(sample_index: int, difficulty) -> tuple[int, int]:
    offset = _DIFFICULTY_OFFSETS[difficulty]
    return _PROFILE_CYCLE[(int(sample_index) + offset) % len(_PROFILE_CYCLE)]


def _draw_exact_profile_axis(ctx, name: str, scheduled, options: tuple[int, ...]) -> int:
    """Record a deterministic schedule value while accepting every legal override.

    GenCtx intentionally has no unkeyed public recording method.  A singleton
    draw records the scheduled default honestly; the full option set is used
    whenever the caller supplies the axis so every declared boundary remains
    valid at every sample index.
    """
    choices = options if name in ctx.overrides else (scheduled,)
    return int(ctx.draw_choice(name, choices))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_w, scheduled_n = _scheduled_profile(sample_index, difficulty)
    width = _draw_exact_profile_axis(ctx, "grid_w", scheduled_w, (19, 29))
    n_seed = _draw_exact_profile_axis(
        ctx, "n_seed_cells", scheduled_n, (2, 3)
    )

    colors = list(
        ctx.draw_distinct_colors("seed_colors", n=n_seed, exclude={0})
    )
    # Every five-demo lesson contains one descending sequence, which
    # falsifies the tempting "sort colors before cycling" shortcut, while the
    # other four indices preserve the full random color-order distribution.
    if (int(sample_index) + _DIFFICULTY_OFFSETS[difficulty]) % 5 == 0:
        colors.sort(reverse=True)

    grid = full_grid(3, width, 0)
    for column, color in zip(_TRIANGULAR_COLUMNS, colors):
        grid[1][column] = color
    return grid


def _grid_shape_error(grid) -> str | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return "grid must be a non-empty list of rows"
    width = len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return "grid must be rectangular and non-empty"
    return None


def _seed_cells(grid) -> list[tuple[int, int]]:
    return [(column, value) for column, value in enumerate(grid[1]) if value != 0]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact canonical teaching grammar without mutating input."""
    del difficulty, meta
    shape_error = _grid_shape_error(grid)
    if shape_error:
        return [shape_error]

    errors: list[str] = []
    height, width = len(grid), len(grid[0])
    if height != 3:
        errors.append(f"expected exactly 3 rows, found {height}")
        return errors
    if width not in (19, 29):
        errors.append(f"width {width} must be 19 or 29")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors
    if any(value != 0 for value in grid[0]):
        errors.append("row 0 must be entirely background color 0")
    if any(value != 0 for value in grid[2]):
        errors.append("row 2 must be entirely background color 0")

    seeds = _seed_cells(grid)
    n_seed = len(seeds)
    if n_seed not in (2, 3):
        errors.append(f"row 1 must contain exactly 2 or 3 seeds, found {n_seed}")
    else:
        actual_columns = [column for column, _ in seeds]
        expected_columns = list(_TRIANGULAR_COLUMNS[:n_seed])
        if actual_columns != expected_columns:
            errors.append(
                f"seed columns {actual_columns} must equal the first {n_seed} "
                f"triangular columns {expected_columns}"
            )
        colors = [value for _, value in seeds]
        if len(set(colors)) != len(colors):
            errors.append("seed colors must be distinct")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    shape_error = _grid_shape_error(grid)
    if shape_error or len(grid) != 3:
        raise ValueError(shape_error or "expected exactly 3 rows")
    return {
        "grid_w": len(grid[0]),
        "n_seed_cells": len(_seed_cells(grid)),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    shape_error = _grid_shape_error(grid)
    if shape_error or len(grid) < 2:
        raise ValueError(shape_error or "grid has no row 1")
    seed = [value for value in grid[1] if value != 0]
    if not seed:
        raise ValueError("row 1 has no nonzero seed colors")
    output = copy.deepcopy(grid)
    width = len(output[0])
    k = 0
    while True:
        column = k * (k + 1) // 2
        if column >= width:
            return output
        output[1][column] = seed[k % len(seed)]
        k += 1


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md, v1)
# ---------------------------------------------------------------------------


def strict_canonical_like(grid) -> list[str]:
    """The lawful generated manifold is intentionally the canonical manifold."""
    return self_check(grid)


def _witness_two_seed_cycle(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["n_seed_cells"] == 2


def _witness_three_seed_cycle(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["n_seed_cells"] == 3


def _witness_width_19(grid) -> bool:
    return not self_check(grid) and len(grid[0]) == 19


def _witness_width_29(grid) -> bool:
    return not self_check(grid) and len(grid[0]) == 29


def _witness_descending_seed_order(grid) -> bool:
    if self_check(grid):
        return False
    colors = [value for _, value in _seed_cells(grid)]
    return colors == sorted(colors, reverse=True)


def _witness_gapped_third_seed(grid) -> bool:
    if self_check(grid):
        return False
    return len(_seed_cells(grid)) == 3 and grid[1][2] == 0 and grid[1][3] != 0


SEMANTIC_WITNESSES = {
    "two_seed_cycle": _witness_two_seed_cycle,
    "three_seed_cycle": _witness_three_seed_cycle,
    "width_19": _witness_width_19,
    "width_29": _witness_width_29,
    "descending_seed_order": _witness_descending_seed_order,
    "gapped_third_seed": _witness_gapped_third_seed,
}


def _seed_sequence(grid) -> list[int]:
    return [value for value in grid[1] if value != 0]


def _paint_positions(
    grid: list[list[int]], sequence: list[int], position: Callable[[int], int]
) -> list[list[int]] | None:
    if not sequence:
        return None
    output = copy.deepcopy(grid)
    width = len(output[0])
    for k in range(64):
        column = position(k)
        if column >= width:
            return output
        if column < 0:
            return None
        output[1][column] = sequence[k % len(sequence)]
    return None


def _competitor_fixed_period_2(grid):
    seed = _seed_sequence(grid)
    return _paint_positions(grid, seed[:2], lambda k: k * (k + 1) // 2)


def _competitor_fixed_period_3(grid):
    seed = _seed_sequence(grid)
    sequence = (seed + [seed[-1]] * 3)[:3] if seed else []
    return _paint_positions(grid, sequence, lambda k: k * (k + 1) // 2)


def _competitor_sorted_colors(grid):
    return _paint_positions(
        grid, sorted(_seed_sequence(grid)), lambda k: k * (k + 1) // 2
    )


def _competitor_repeat_first(grid):
    seed = _seed_sequence(grid)
    return _paint_positions(grid, seed[:1], lambda k: k * (k + 1) // 2)


def _competitor_square_positions(grid):
    return _paint_positions(grid, _seed_sequence(grid), lambda k: k * k)


def _competitor_consecutive_positions(grid):
    return _paint_positions(grid, _seed_sequence(grid), lambda k: k)


_LESSON_COMPETITORS = {
    "always use a two-color period": _competitor_fixed_period_2,
    "always use a three-color period": _competitor_fixed_period_3,
    "sort seed colors before cycling": _competitor_sorted_colors,
    "repeat only the first marker color": _competitor_repeat_first,
    "paint square-number rather than triangular columns": _competitor_square_positions,
    "paint consecutive rather than triangular columns": _competitor_consecutive_positions,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a plausible shortcut survives every demonstration."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(f"demo {index} output does not match the triangular cycle rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        competitor_answer = competitor(query["input"])
        if survives and competitor_answer != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Named task-local impostors that structural self_check must reject."""
    valid = generate(7001, 0, difficulty="easy", grid_w=19, n_seed_cells=3)
    fixtures: list[tuple[str, list[list[int]]]] = []

    outer_row_marker = copy.deepcopy(valid)
    outer_row_marker[0][5] = 4
    fixtures.append(("outer_row_marker", outer_row_marker))

    non_triangular_seed = copy.deepcopy(valid)
    non_triangular_seed[1][3] = 0
    non_triangular_seed[1][4] = 7
    fixtures.append(("non_triangular_seed", non_triangular_seed))

    duplicate_seed_color = copy.deepcopy(valid)
    duplicate_seed_color[1][3] = duplicate_seed_color[1][0]
    fixtures.append(("duplicate_seed_color", duplicate_seed_color))

    extra_seed = copy.deepcopy(valid)
    extra_seed[1][6] = 9
    fixtures.append(("extra_fourth_seed", extra_seed))

    wrong_width = [row[:-1] for row in valid]
    fixtures.append(("wrong_width_18", wrong_width))

    missing_seed = copy.deepcopy(valid)
    missing_seed[1][1] = 0
    fixtures.append(("missing_second_seed", missing_seed))
    return fixtures
