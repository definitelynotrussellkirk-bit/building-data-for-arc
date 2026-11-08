"""Generator for E25 — move each horizontal run's terminal cell right.

The authoritative rule scans row-major into an empty output.  A nonzero cell
moves one column right exactly when its input right-neighbour is zero; otherwise
it stays in place.  Consequently, in every horizontal nonzero run, all cells
except the terminal one stay fixed and the terminal cell shifts into the empty
cell immediately to its right.

Generated lessons always contain both branches: at least one blocked/stationary
cell inside a run and at least one terminal/moving cell.  They also avoid the
right edge so every run has a visible move and the identity rule cannot explain
an accepted ordinary draw.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85305305afdf"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "dfecf6d0b7a6"

SUMMARY = (
    "For each horizontal nonzero run, keep its blocked prefix fixed and move "
    "only its terminal cell one position right into the adjacent zero."
)

INVARIANTS = [
    "background is 0",
    "every generated scene contains at least one horizontal run of length at least 2",
    "every nonzero run ends before the right edge and is followed by 0",
    "ordinary examples exercise both stationary and moving branches",
    "the number of nonzero cells and distinct nonzero colors matches the declared axes",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "3..12"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "4..16"},
    "cells": {"type": "int", "default": "difficulty-aware", "valid": "3..12"},
    "n_distinct_colors": {"type": "int", "default": "difficulty-aware", "valid": "1..9"},
}

_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIFFICULTY_BANDS = {
    None: {"grid_h": (4, 9), "grid_w": (6, 13), "cells": (4, 10), "colors": (2, 6)},
    "easy": {"grid_h": (3, 5), "grid_w": (4, 8), "cells": (3, 6), "colors": (1, 3)},
    "medium": {"grid_h": (5, 8), "grid_w": (7, 12), "cells": (5, 9), "colors": (2, 6)},
    "hard": {"grid_h": (8, 12), "grid_w": (11, 16), "cells": (8, 12), "colors": (4, 9)},
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
    """Use full declared bounds for explicit overrides, a difficulty band otherwise."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, global_lo, global_hi)
    lo, hi = default_band
    return ctx.draw_int_strict(label, lo, hi)


def _composition(total: int, parts: int, cap: int, rng) -> list[int]:
    """Random positive composition with each part <= cap and one part >= 2."""
    if parts < 1 or parts > total or total > parts * cap:
        raise ValueError("requested cells do not fit the selected grid")
    values = [1] * parts
    remaining = total - parts
    order = list(range(parts))
    rng.shuffle(order)
    while remaining:
        eligible = [index for index in order if values[index] < cap]
        if not eligible:
            raise ValueError("requested cells do not fit the selected run count")
        index = rng.choice(eligible)
        values[index] += 1
        remaining -= 1
    if max(values) < 2:
        raise ValueError("at least one blocked cell is required")
    rng.shuffle(values)
    return values


def rule_mirror(grid):
    """Pure Python mirror of the exact selected Racket rule."""
    if not _valid_arc_grid(grid):
        raise ValueError("rule input must be a nonempty rectangular ARC grid")
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            if col + 1 < width and grid[row][col + 1] == 0:
                if out[row][col + 1] == 0:
                    out[row][col + 1] = value
            elif out[row][col] == 0:
                out[row][col] = value
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the teaching grammar while accepting all canonical examples."""
    if not _valid_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC-color matrix"]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    nonzero = [(row, col) for row in range(height) for col in range(width) if grid[row][col] != 0]
    if len(nonzero) < 3:
        errors.append("grid must contain at least three nonzero cells")
    if any(col == width - 1 for _, col in nonzero):
        errors.append("nonzero cells must avoid the right edge")
    movable = [
        (row, col)
        for row, col in nonzero
        if col + 1 < width and grid[row][col + 1] == 0
    ]
    blocked = [
        (row, col)
        for row, col in nonzero
        if col + 1 < width and grid[row][col + 1] != 0
    ]
    if not movable:
        errors.append("grid must contain at least one terminal cell with an empty right neighbour")
    if not blocked:
        errors.append("grid must contain at least one blocked/stationary cell inside a run")
    if nonzero and rule_mirror(grid) == grid:
        errors.append("canonical rule must change the accepted grid")
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
    bands = _DIFFICULTY_BANDS[difficulty]
    height = _axis_int(ctx, "grid_h", 3, 12, bands["grid_h"])
    width = _axis_int(ctx, "grid_w", 4, 16, bands["grid_w"])

    capacity = height * (width - 1)
    default_cells = (bands["cells"][0], min(bands["cells"][1], 12, capacity))
    if default_cells[1] < default_cells[0]:
        default_cells = (3, min(12, capacity))
    cells = _axis_int(ctx, "cells", 3, 12, default_cells)
    if cells > capacity:
        raise ValueError(
            f"cells={cells} exceeds one-run-per-row capacity {capacity} for {height}x{width}"
        )

    color_default = (bands["colors"][0], min(bands["colors"][1], 9, cells))
    if color_default[1] < color_default[0]:
        color_default = (1, min(9, cells))
    n_colors = _axis_int(ctx, "n_distinct_colors", 1, 9, color_default)
    if n_colors > cells:
        raise ValueError("n_distinct_colors cannot exceed cells")

    rng = ctx.draw_rng("layout")
    min_runs = 2
    max_runs = min(height, cells - 1)
    feasible_runs = [
        count
        for count in range(min_runs, max_runs + 1)
        if cells <= count * (width - 1)
    ]
    if not feasible_runs:
        raise ValueError("selected grid cannot realize both moving and blocked branches")
    run_count = rng.choice(feasible_runs)
    lengths = _composition(cells, run_count, width - 1, rng)
    rows = rng.sample(range(height), run_count)

    colors = list(ctx.draw_distinct_colors("colors", n=n_colors, exclude=(0,)))
    assignments = colors[:]
    assignments.extend(rng.choice(colors) for _ in range(cells - len(colors)))
    rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    cursor = 0
    for row, length in zip(rows, lengths):
        start = rng.randint(0, width - length - 1)
        for col in range(start, start + length):
            grid[row][col] = assignments[cursor]
            cursor += 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid
