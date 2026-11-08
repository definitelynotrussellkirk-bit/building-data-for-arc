"""Generator for ``ebe7614a49f4`` — row/column activation map.

A blue(1) cell activates its row and a red(2) cell activates its column.
The reference rule emits a fresh grid with green(3) at every active-row ×
active-column intersection.  The marker cells themselves are not copied.

The repaired controls are deliberately small and observable: dimensions,
active-row/column counts, marker redundancy, and marker layout.  Every random
decision is keyed through :class:`GenCtx`; unknown or coercive overrides fail
closed.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ebe7614a49f4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
SUMMARY = (
    "Blue(1) cells activate rows and red(2) cells activate columns. A fresh "
    "same-size output paints green(3) at every active-row/active-column "
    "intersection and black(0) elsewhere."
)
EXAMPLES_NEEDED = 3

LAYOUTS = ("scattered", "boundary_contacts", "crossed_markers")
_ALLOWED_OVERRIDES = {
    "grid_h",
    "grid_w",
    "n_active_rows",
    "n_active_cols",
    "marker_redundancy",
    "layout",
}

INVARIANTS = [
    "background is 0",
    "at least one blue(1) row marker",
    "at least one red(2) column marker",
    "all marker cells are distinct",
    "the output rule is active rows × active columns in green(3)",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 6..30", "valid": "6..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware 6..30", "valid": "6..30"},
    "n_active_rows": {"type": "int", "default": "difficulty-aware 1..5", "valid": "1..min(5, grid_h)"},
    "n_active_cols": {"type": "int", "default": "difficulty-aware 1..5", "valid": "1..min(5, grid_w)"},
    "marker_redundancy": {"type": "int", "default": "1..2", "valid": "1..2"},
    "layout": {"type": "str", "default": "rng", "valid": "|".join(LAYOUTS)},
}


def _validate_difficulty(difficulty) -> None:
    if difficulty is None:
        return
    if isinstance(difficulty, str):
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be easy, medium, hard, a number in 0..1, or None")
        return
    if type(difficulty) in (int, float) and not isinstance(difficulty, bool):
        if 0.0 <= float(difficulty) <= 1.0:
            return
    raise ValueError("difficulty must be easy, medium, hard, a number in 0..1, or None")


def _bands(difficulty) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 10), (1, 3)
    if difficulty == "medium":
        return (9, 18), (2, 4)
    if difficulty == "hard":
        return (16, 30), (3, 5)
    if type(difficulty) in (int, float) and difficulty is not None:
        value = float(difficulty)
        if value < 0.34:
            return (6, 12), (1, 3)
        if value < 0.67:
            return (10, 21), (2, 4)
        return (16, 30), (3, 5)
    return (7, 20), (2, 4)


def _priority(values: Iterable[int], preferred: Iterable[int], rng) -> list[int]:
    preferred_unique = []
    seen = set()
    for value in preferred:
        if value in values and value not in seen:
            preferred_unique.append(value)
            seen.add(value)
    rest = [value for value in values if value not in seen]
    # Preserve caller-supplied priorities (notably guaranteed boundary cells);
    # randomize only the fallback pool.
    rng.shuffle(rest)
    return preferred_unique + rest


def _draw_int_with_declared_override_range(
    ctx,
    overrides: dict,
    label: str,
    default_bounds: tuple[int, int],
    declared_bounds: tuple[int, int],
) -> int:
    """Use difficulty bands for sampling, but the declared axis for overrides."""
    bounds = (
        declared_bounds
        if label in overrides and overrides[label] is not None
        else default_bounds
    )
    return ctx.draw_int_strict(label, *bounds)


def _take_free(candidates: list[tuple[int, int]], count: int, used: set[tuple[int, int]]) -> list[tuple[int, int]]:
    selected = []
    for cell in candidates:
        if cell not in used:
            selected.append(cell)
            used.add(cell)
            if len(selected) == count:
                return selected
    raise ValueError("requested marker configuration does not fit the selected grid")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    _validate_difficulty(difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size_band, count_band = _bands(difficulty)
    h = _draw_int_with_declared_override_range(
        ctx, overrides, "grid_h", size_band, (6, 30)
    )
    w = _draw_int_with_declared_override_range(
        ctx, overrides, "grid_w", size_band, (6, 30)
    )
    row_hi = min(5, h)
    col_hi = min(5, w)
    row_lo = min(count_band[0], row_hi)
    col_lo = min(count_band[0], col_hi)
    n_rows = _draw_int_with_declared_override_range(
        ctx,
        overrides,
        "n_active_rows",
        (row_lo, min(count_band[1], row_hi)),
        (1, row_hi),
    )
    n_cols = _draw_int_with_declared_override_range(
        ctx,
        overrides,
        "n_active_cols",
        (col_lo, min(count_band[1], col_hi)),
        (1, col_hi),
    )
    redundancy = ctx.draw_int_strict("marker_redundancy", 1, 2)
    layout = ctx.draw_choice("layout", LAYOUTS)

    rng = ctx.draw_rng("marker-layout")
    active_rows = sorted(rng.sample(range(h), n_rows))
    active_cols = sorted(rng.sample(range(w), n_cols))
    inactive_rows = [row for row in range(h) if row not in active_rows]
    inactive_cols = [col for col in range(w) if col not in active_cols]

    grid = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    blue_crossings = {col: 0 for col in active_cols}

    for index, row in enumerate(active_rows):
        if layout == "crossed_markers":
            # Leave ``redundancy`` cells free in every active column for its
            # red markers.  Without this reservation, dense 6x6 cases can
            # saturate a column with blue markers before red placement.
            crossing_cols = [
                col
                for col in active_cols
                if blue_crossings[col] < h - redundancy
            ]
            fallback_cols = list(inactive_cols)
            rng.shuffle(crossing_cols)
            rng.shuffle(fallback_cols)
            cols = crossing_cols + fallback_cols
        else:
            preferred = list(inactive_cols)
            if layout == "boundary_contacts" and index == 0:
                preferred = [0, w - 1, *preferred]
            cols = _priority(range(w), preferred, rng)
        cells = _take_free([(row, col) for col in cols], redundancy, used)
        for rr, cc in cells:
            grid[rr][cc] = 1
            if cc in blue_crossings:
                blue_crossings[cc] += 1

    for index, col in enumerate(active_cols):
        if layout == "crossed_markers":
            preferred = list(active_rows)
        else:
            preferred = list(inactive_rows)
        if layout == "boundary_contacts" and index == 0:
            preferred = [0, h - 1, *preferred]
        rows = _priority(range(h), preferred, rng)
        cells = _take_free([(row, col) for row in rows], redundancy, used)
        for rr, cc in cells:
            grid[rr][cc] = 2

    return grid


def _checked_grid(grid) -> list[list[int]]:
    if type(grid) is not list or not grid or len(grid) > 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not grid[0] or len(grid[0]) > 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in (0, 1, 2) for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0, 1, and 2")
    return [list(row) for row in grid]


def rule_mirror(grid) -> list[list[int]]:
    checked = _checked_grid(grid)
    active_rows = {row for row, values in enumerate(checked) if 1 in values}
    active_cols = {
        col
        for col in range(len(checked[0]))
        if any(row[col] == 2 for row in checked)
    }
    output = full_grid(len(checked), len(checked[0]), 0)
    for row in active_rows:
        for col in active_cols:
            output[row][col] = 3
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    try:
        checked = _checked_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if not any(value == 1 for row in checked for value in row):
        errors.append("missing blue(1) row marker")
    if not any(value == 2 for row in checked for value in row):
        errors.append("missing red(2) column marker")
    return errors
