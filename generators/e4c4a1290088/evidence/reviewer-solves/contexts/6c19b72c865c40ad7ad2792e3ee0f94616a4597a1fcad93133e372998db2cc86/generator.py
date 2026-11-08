"""Generator for ARC task e4c4a1290088 — equality matrix from headers.

The first row and first column are label headers over an empty interior.  For
an interior cell ``(r, c)``, copy the column header ``grid[0][c]`` exactly when
it equals the row header ``grid[r][0]``; otherwise leave color 0.  Both header
strips are preserved.

The default curriculum deliberately includes the three official shape/palette
profiles in every difficulty band, while every generated scene also contains
an off-diagonal match, at least two labels, and a nonzero mismatch.  Those
features falsify diagonal-only, first-label-only, and any-nonzero-pair
shortcuts in every lesson.
"""
from __future__ import annotations

from copy import deepcopy
from numbers import Real
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e4c4a1290088"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b1a9cb7a0f30"

SUMMARY = (
    "Row 0 and column 0 are label headers over a color-0 interior. For each "
    "interior cell, copy its column header exactly when that color equals the "
    "row header; otherwise keep 0. Preserve both header strips."
)

INVARIANTS = [
    "the shared top-left corner and every input interior cell are color 0",
    "row and column headers use the same set of two to five nonzero labels",
    "every nonzero label appears in both header strips",
    "an off-diagonal equal-label pair makes the equality relation explicit",
    "a nonzero unequal-label pair makes the mismatch branch explicit",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.50

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three official profiles plus difficulty-scaled broad draws",
        "valid": "6..18",
        "doc": "Exact returned grid height; every value is legal in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "three official profiles plus difficulty-scaled broad draws",
        "valid": "6..18",
        "doc": "Exact returned grid width; every value is legal in every band.",
    },
    "n_labels": {
        "type": "int",
        "default": "official counts 2/3 plus difficulty-scaled broad draws",
        "valid": "2..5",
        "doc": "Exact number of distinct nonzero labels present in both headers.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_CANONICAL_PROFILES = ((6, 6, 3), (7, 7, 2), (8, 8, 3))
_AXIS_BOUNDS = {"grid_h": (6, 18), "grid_w": (6, 18), "n_labels": (2, 5)}


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty in (None, "easy", "medium", "hard"):
        return
    if isinstance(difficulty, Real) and not isinstance(difficulty, bool):
        value = float(difficulty)
        if 0.0 <= value <= 1.0:
            return
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or type(value) is not int:
            raise TypeError(f"{name} override must be an integer, got {value!r}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _broad_bounds(axis: str, difficulty: Any) -> tuple[int, int]:
    if isinstance(difficulty, Real) and not isinstance(difficulty, bool):
        return _AXIS_BOUNDS[axis]
    band = "medium" if difficulty is None else difficulty
    table = {
        "grid_h": {"easy": (6, 10), "medium": (8, 14), "hard": (12, 18)},
        "grid_w": {"easy": (6, 10), "medium": (8, 14), "hard": (12, 18)},
        "n_labels": {"easy": (2, 3), "medium": (2, 4), "hard": (3, 5)},
    }
    return table[axis][band]


def _draw_axis(ctx, overrides: dict[str, Any], axis: str, preferred: int | None) -> int:
    lo, hi = _AXIS_BOUNDS[axis]
    if overrides.get(axis) is not None:
        # Full declared domain in every difficulty band: exact-or-loud overrides.
        return ctx.draw_int(axis, lo, hi)
    if preferred is not None:
        # A fixed bound still records honest keyed provenance for the exact axis.
        return ctx.draw_int(axis, preferred, preferred)
    broad_lo, broad_hi = _broad_bounds(axis, ctx.difficulty)
    return ctx.draw_int_diff(axis, broad_lo, broad_hi)


def _header_values(
    length: int,
    labels: tuple[int, ...],
    rng,
    *,
    allow_zero: bool,
    force_zero: bool,
) -> list[int]:
    values = list(labels)
    if force_zero and len(values) < length:
        values.append(0)
    choices = list(labels) + ([0] if allow_zero else [])
    while len(values) < length:
        values.append(rng.choice(choices))
    rng.shuffle(values)
    return values


def _move_first(values: list[int], value: int, target: int) -> None:
    source = values.index(value)
    values[source], values[target] = values[target], values[source]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input grid with deterministic keyed randomness."""
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_index = int(sample_index) % 4
    preferred = _CANONICAL_PROFILES[profile_index] if profile_index < 3 else None
    h = _draw_axis(ctx, overrides, "grid_h", None if preferred is None else preferred[0])
    w = _draw_axis(ctx, overrides, "grid_w", None if preferred is None else preferred[1])
    n_labels = _draw_axis(
        ctx, overrides, "n_labels", None if preferred is None else preferred[2]
    )

    labels = ctx.draw_distinct_colors("label_colors", n=n_labels, exclude=(0,))
    rng = ctx.draw_rng("header_layout")

    # Official 6x6 has no repeated zero header; 7x7 and 8x8 do.  Broad draws
    # vary this harmless feature while preserving the nonzero teaching signal.
    if profile_index == 0:
        allow_zero = force_zero = False
    elif profile_index in (1, 2):
        allow_zero = force_zero = True
    else:
        allow_zero = bool(rng.randrange(2))
        force_zero = allow_zero and min(h - 1, w - 1) > n_labels

    row_headers = _header_values(
        w - 1, labels, rng, allow_zero=allow_zero, force_zero=force_zero
    )
    col_headers = _header_values(
        h - 1, labels, rng, allow_zero=allow_zero, force_zero=force_zero
    )

    # Construct an explicit off-diagonal equality witness without changing any
    # label counts: (row 2, column 1) carries labels[0] on both headers.
    _move_first(row_headers, labels[0], 0)
    _move_first(col_headers, labels[0], 1)

    grid = full_grid(h, w, 0)
    grid[0][1:] = row_headers
    for row, value in enumerate(col_headers, start=1):
        grid[row][0] = value
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or type(value) is not int or not 0 <= value <= 9:
                return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _header_analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    row_headers = list(grid[0][1:])
    col_headers = [grid[row][0] for row in range(1, h)]
    row_labels = set(row_headers) - {0}
    col_labels = set(col_headers) - {0}
    off_diagonal_match = any(
        row != column and row_value == column_value != 0
        for row, row_value in enumerate(col_headers, start=1)
        for column, column_value in enumerate(row_headers, start=1)
    )
    nonzero_mismatch = any(
        row_value != 0 and column_value != 0 and row_value != column_value
        for row_value in col_headers
        for column_value in row_headers
    )
    return {
        "errors": [],
        "height": h,
        "width": w,
        "row_headers": row_headers,
        "col_headers": col_headers,
        "row_labels": row_labels,
        "col_labels": col_labels,
        "labels": row_labels | col_labels,
        "off_diagonal_match": off_diagonal_match,
        "nonzero_mismatch": nonzero_mismatch,
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the canonical input grammar and reject shortcut-hiding scenes."""
    del difficulty, meta
    analysis = _header_analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    h, w = analysis["height"], analysis["width"]
    if not 6 <= h <= 18 or not 6 <= w <= 18:
        errors.append("grid dimensions must each be between 6 and 18")
    if grid[0][0] != 0:
        errors.append("shared header corner must be color 0")
    if any(grid[row][column] != 0 for row in range(1, h) for column in range(1, w)):
        errors.append("input interior must be entirely color 0")
    if analysis["row_labels"] != analysis["col_labels"]:
        errors.append("row and column headers must contain the same nonzero labels")
    if not 2 <= len(analysis["labels"]) <= 5:
        errors.append("headers must use between two and five nonzero labels")
    if not analysis["off_diagonal_match"]:
        errors.append("need an off-diagonal nonzero equality witness")
    if not analysis["nonzero_mismatch"]:
        errors.append("need a nonzero unequal-label witness")
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    analysis = _header_analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_labels": len(analysis["labels"]),
    }


def oracle_output(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket program."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = deepcopy([list(row) for row in grid])
    for row in range(1, len(grid)):
        for column in range(1, len(grid[0])):
            output[row][column] = (
                grid[0][column]
                if grid[row][0] == grid[0][column]
                else 0
            )
    return output


def strict_canonical_like(grid: Any) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = (
        len(grid),
        len(grid[0]),
        len((set(grid[0][1:]) | {grid[row][0] for row in range(1, len(grid))}) - {0}),
    )
    if signature not in _CANONICAL_PROFILES:
        return [f"profile {signature!r} is outside the three official profiles"]
    return []


def _copy_or_empty(grid: Any) -> list[list[int]]:
    if _rectangular_errors(grid):
        return []
    return [list(row) for row in grid]


def _rival_diagonal_only(grid: Any) -> list[list[int]]:
    output = _copy_or_empty(grid)
    if not output:
        return output
    for row in range(1, len(output)):
        for column in range(1, len(output[0])):
            output[row][column] = (
                grid[0][column]
                if row == column and grid[row][0] == grid[0][column]
                else 0
            )
    return output


def _rival_first_label_only(grid: Any) -> list[list[int]]:
    output = _copy_or_empty(grid)
    if not output:
        return output
    first_label = next((value for value in grid[0][1:] if value != 0), None)
    for row in range(1, len(output)):
        for column in range(1, len(output[0])):
            output[row][column] = (
                first_label
                if first_label is not None
                and grid[row][0] == first_label
                and grid[0][column] == first_label
                else 0
            )
    return output


def _rival_any_nonzero_pair(grid: Any) -> list[list[int]]:
    output = _copy_or_empty(grid)
    if not output:
        return output
    for row in range(1, len(output)):
        for column in range(1, len(output[0])):
            output[row][column] = (
                grid[0][column]
                if grid[row][0] != 0 and grid[0][column] != 0
                else 0
            )
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "diagonal_only": _rival_diagonal_only,
    "first_label_only": _rival_first_label_only,
    "any_nonzero_pair": _rival_any_nonzero_pair,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def _valid_and_disagrees(grid: Any, rival: Callable[[Any], list[list[int]]]) -> bool:
    return self_check(grid) == [] and rival(grid) != oracle_output(grid)


SEMANTIC_WITNESSES = {
    "off_diagonal_equality": lambda grid: _valid_and_disagrees(grid, _rival_diagonal_only),
    "multiple_labels": lambda grid: _valid_and_disagrees(grid, _rival_first_label_only),
    "nonzero_mismatch": lambda grid: _valid_and_disagrees(grid, _rival_any_nonzero_pair),
}
WITNESS_RIVALS = {
    "off_diagonal_equality": ["diagonal_only"],
    "multiple_labels": ["first_label_only"],
    "nonzero_mismatch": ["any_nonzero_pair"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named plausible shortcut survives all demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output")
            continue
        if self_check(pair["input"]):
            reasons.append(f"{label} input is outside the generator grammar")
            continue
        if oracle_output(pair["input"]) != pair["output"]:
            reasons.append(f"{label} output disagrees with the equality-matrix rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
