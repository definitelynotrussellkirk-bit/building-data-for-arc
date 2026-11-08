"""Generator for 1ec277b81469 — right-pack every row, preserving order.

Each row is transformed independently.  Its nonzero values are read from left to
right and rewritten as a contiguous suffix at the right edge; zeros fill the
prefix.  Empty rows remain empty.

The ordinary generator exposes only controls it can honor exactly.  Every
accepted generated scene has at least two active rows, at least one multi-cell
row, and a visible canonical change.  Explicit controls are strict (no Boolean,
float, or string coercion) and contradictory requests fail loudly.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ec277b81469"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6ab6552b1d13"

SUMMARY = (
    "Independently in each row, collect the nonzero cells in left-to-right order "
    "and place that sequence flush against the right edge, leaving zeros on the left."
)

INVARIANTS = [
    "background is 0",
    "at least two rows are active",
    "at least one active row contains multiple cells so order preservation is visible",
    "ordinary generated rows avoid the right edge, so right-packing changes the grid",
    "requested shape, active-row count, total cell count, and distinct-color count are exact",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "4..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "5..18"},
    "active_rows": {"type": "int", "default": "difficulty-aware", "valid": "2..14"},
    "cells": {"type": "int", "default": "difficulty-aware", "valid": "3..238"},
    "n_distinct_colors": {"type": "int", "default": "difficulty-aware", "valid": "1..9"},
}

_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIFFICULTY_BANDS = {
    None: {"grid_h": (5, 10), "grid_w": (7, 14), "active_cap": 7, "cells_per_row": 5, "colors": (2, 4)},
    "easy": {"grid_h": (4, 6), "grid_w": (5, 9), "active_cap": 4, "cells_per_row": 3, "colors": (1, 3)},
    "medium": {"grid_h": (6, 10), "grid_w": (9, 14), "active_cap": 7, "cells_per_row": 6, "colors": (2, 6)},
    "hard": {"grid_h": (10, 14), "grid_w": (14, 18), "active_cap": 12, "cells_per_row": 11, "colors": (4, 9)},
}


def _valid_arc_grid(grid) -> bool:
    return (
        type(grid) is list
        and bool(grid)
        and type(grid[0]) is list
        and bool(grid[0])
        and 1 <= len(grid) <= 30
        and 1 <= len(grid[0]) <= 30
        and all(
            type(row) is list
            and len(row) == len(grid[0])
            and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    )


def _axis_int(ctx, label: str, global_lo: int, global_hi: int, default_band: tuple[int, int]) -> int:
    """Honor explicit values over the full contract and defaults over a safe band."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, global_lo, global_hi)
    lo, hi = default_band
    return ctx.draw_int_strict(label, lo, hi)


def _bounded_composition(total: int, parts: int, minimum: int, maximum: int, rng) -> list[int]:
    if parts < 1 or minimum < 0 or maximum < minimum:
        raise ValueError("invalid composition bounds")
    if not parts * minimum <= total <= parts * maximum:
        raise ValueError("cells do not fit the selected active rows and width")
    values = [minimum] * parts
    remaining = total - parts * minimum
    while remaining:
        eligible = [index for index, value in enumerate(values) if value < maximum]
        if not eligible:
            raise ValueError("cells do not fit the selected active rows and width")
        values[rng.choice(eligible)] += 1
        remaining -= 1
    rng.shuffle(values)
    return values


def rule_mirror(grid):
    """Pure Python mirror of the unique selected Racket rule."""
    if not _valid_arc_grid(grid):
        raise ValueError("rule input must be a nonempty rectangular ARC grid")
    width = len(grid[0])
    output = []
    for row in grid:
        values = [value for value in row if value != 0]
        output.append([0] * (width - len(values)) + values)
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate a nontrivial teaching domain while retaining all canonical pairs."""
    if not _valid_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC-color matrix"]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid too large: {height}x{width}")
        return errors
    active = [row for row in grid if any(value != 0 for value in row)]
    if len(active) < 2:
        errors.append(f"expected at least two active rows, got {len(active)}")
    if not any(sum(value != 0 for value in row) >= 2 for row in active):
        errors.append("expected at least one multi-cell row to expose order preservation")
    if sum(value != 0 for row in grid for value in row) < 3:
        errors.append("expected at least three foreground cells")
    if active and rule_mirror(grid) == grid:
        errors.append("canonical right-packing must change the accepted grid")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, easy, medium, or hard")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = _DIFFICULTY_BANDS[difficulty]
    height = _axis_int(ctx, "grid_h", 4, 14, band["grid_h"])
    width = _axis_int(ctx, "grid_w", 5, 18, band["grid_w"])

    active_rows = _axis_int(ctx, "active_rows", 2, 14, (2, min(height, band["active_cap"])))
    if active_rows > height:
        raise ValueError(f"active_rows={active_rows} exceeds grid_h={height}")

    capacity = active_rows * (width - 1)
    minimum_cells = active_rows + 1
    default_max = min(capacity, active_rows * min(width - 1, band["cells_per_row"]))
    cells = _axis_int(ctx, "cells", 3, 238, (minimum_cells, max(minimum_cells, default_max)))
    if not minimum_cells <= cells <= capacity:
        raise ValueError(
            f"cells={cells} must be in {minimum_cells}..{capacity} for "
            f"active_rows={active_rows} and grid_w={width}"
        )

    color_lo, color_hi = band["colors"]
    color_hi = min(color_hi, 9, cells)
    color_lo = min(color_lo, color_hi)
    n_colors = _axis_int(ctx, "n_distinct_colors", 1, 9, (color_lo, color_hi))
    if n_colors > cells:
        raise ValueError("n_distinct_colors cannot exceed cells")

    rng = ctx.draw_rng("layout")
    row_lengths = _bounded_composition(cells, active_rows, 1, width - 1, rng)
    rows = rng.sample(range(height), active_rows)
    colors = list(ctx.draw_distinct_colors("colors", n=n_colors, exclude={0}))

    assignments = colors[:]
    assignments.extend(rng.choice(colors) for _ in range(cells - len(colors)))
    rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    cursor = 0
    for row, length in zip(rows, row_lengths):
        positions = sorted(rng.sample(range(width - 1), length))
        for col in positions:
            grid[row][col] = assignments[cursor]
            cursor += 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid
