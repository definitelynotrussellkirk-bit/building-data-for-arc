"""Generator for arc_puzzle_bank_fourth21:E24.

Rule (verified against canonical program_solution): each horizontal run
of EXACTLY length 3 is extended by one cell on each side (the cells
immediately left and right are painted the run's own color, when those
flanks are bg-0). The transform is COLOR-INDEPENDENT — every qualifying
3-run grows to length 5 in its own color. Runs of other lengths are left
unchanged.

Ordinary lessons contain both actionable length-3 runs and an isolated
length-4 no-op run. This canonical negative distinguishes the exact-length
rule from the overgeneralized shortcut that extends every horizontal run.
Degenerates: no_runs, run_too_long, runs_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a2fc4c442e35"
VERSION = "2.2.0"
TASK_ID = "a2fc4c442e35"
SUMMARY = (
    "0-bg grid (h~5-8, w~8-12) with 1-3 isolated horizontal length-3 "
    "target runs and one isolated horizontal length-4 negative run. Every "
    "run uses a distinct non-zero color and a distinct row, with blank cells "
    "immediately on both sides. The rule extends each exact-length-3 run by "
    "one same-colored cell on the left and right, while the length-4 run "
    "stays unchanged. The mixed lesson refutes the shortcut that extends "
    "every non-zero horizontal run regardless of length."
)

INVARIANTS = [
    "background is 0",
    "each ordinary grid has at least one horizontal length-3 target run",
    "each ordinary grid has at least one horizontal length-4 no-op run",
    "the cells immediately left and right of every run are zero",
    "runs use distinct rows and colors to avoid accidental merging",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_runs", "run_too_long", "runs_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "5..8"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "8..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "runs":           {"type": "int", "default": "difficulty-aware target triples 1..3",
                       "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "target runs plus one negative",
                       "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "row_separated", "valid": "row_separated"},
    "n_distinct_colors": {"type": "int", "default": "target runs plus one negative",
                          "valid": "2..4"},
    "run_density":    {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the mixed exact-triple teaching grammar.

    Ordinary grids contain only isolated horizontal runs of length 3 or 4,
    with at least one of each class. Length-3 runs are actionable targets;
    length-4 runs are canonical no-op negatives.
    """
    del difficulty, meta
    if not grid or not grid[0]:
        return ["empty grid"]
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]

    errors = []
    runs = []
    length_counts = {3: 0, 4: 0}
    for row_index in range(height):
        row_runs = 0
        col = 0
        while col < width:
            value = grid[row_index][col]
            if value == 0:
                col += 1
                continue

            run_start = col
            while col < width and grid[row_index][col] == value:
                col += 1
            run_length = col - run_start
            row_runs += 1
            runs.append((row_index, run_start, col - 1, value))

            if run_length not in length_counts:
                errors.append(
                    f"row {row_index} has run of color {value} length {run_length} "
                    "(expected 3 or 4)"
                )
            else:
                length_counts[run_length] += 1

            if run_start == 0 or grid[row_index][run_start - 1] != 0:
                errors.append(
                    f"row {row_index} run at col {run_start}: left flank is not blank"
                )
            if col >= width or grid[row_index][col] != 0:
                errors.append(
                    f"row {row_index} run at col {run_start}: right flank is not blank"
                )

        if row_runs > 1:
            errors.append(
                f"row {row_index} has {row_runs} runs; expected row-separated runs"
            )

    if not runs:
        errors.append("no non-bg horizontal runs found")
    if length_counts[3] == 0:
        errors.append("missing required length-3 target run")
    if length_counts[4] == 0:
        errors.append("missing required length-4 negative run")
    if len(runs) != len({row for row, *_ in runs}):
        errors.append("multiple runs share a row")
    return errors[:5]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        height = ctx.draw_int("grid_h", 5, 6)
        width = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        height = ctx.draw_int("grid_h", 7, 8)
        width = ctx.draw_int("grid_w", 10, 12)
    else:
        height = ctx.draw_int("grid_h", 5, 8)
        width = ctx.draw_int("grid_w", 8, 12)

    target_count = min(ctx.draw_int_diff("runs", 1, 3), height - 1)
    rng = ctx.draw_rng("layout")
    grid = full_grid(height, width, 0)

    total_runs = target_count + 1
    rows = rng.sample(range(height), total_runs)
    colors = rng.sample(range(1, 10), total_runs)

    for row, color in zip(rows[:target_count], colors[:target_count]):
        start = rng.randint(1, width - 5)
        for offset in range(3):
            grid[row][start + offset] = color

    negative_row = rows[-1]
    negative_color = colors[-1]
    negative_start = rng.randint(1, width - 6)
    for offset in range(4):
        grid[negative_row][negative_start + offset] = negative_color

    return grid


def _draw_from_degenerate(name, rng):
    del rng
    height, width = 6, 10
    grid = full_grid(height, width, 0)
    if name == "no_runs":
        # Empty grid: neither required semantic class is present.
        return grid
    if name == "run_too_long":
        # A legal no-op shape in isolation, but no actionable triple is present.
        for offset in range(4):
            grid[2][2 + offset] = 5
        return grid
    if name == "runs_touching":
        # Two adjacent colored runs violate the blank-flank and row-separation grammar.
        for offset in range(3):
            grid[2][1 + offset] = 4
            grid[2][4 + offset] = 6
        return grid
    return grid
