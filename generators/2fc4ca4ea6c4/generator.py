"""Generator for S8_E2 — every odd horizontal run reduces to its midpoint.

Regular scenes deliberately include both a singleton (already its own midpoint)
and a longer odd run so the canonical identity edge case is taught rather than
left to a degenerate-only texture.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2fc4ca4ea6c4"
VERSION = "2.1.0"
TASK_ID = "2fc4ca4ea6c4"

SUMMARY = (
    "A zero-background grid contains separated same-color horizontal runs of "
    "odd length.  Keep only each run's midpoint cell in its original color and "
    "erase every other cell.  Regular draws include singleton and longer runs."
)

INVARIANTS = [
    "background is 0",
    "every same-color horizontal run has odd length",
    "regular draws contain at least one singleton and one longer run",
    "outputs keep only each run midpoint in the run color",
]

PALETTES = {
    "default": (2, 3, 4, 6, 7),
    "warm": (2, 4, 7, 9, 3),
    "cool": (1, 5, 6, 8, 3),
    "varied": (1, 2, 4, 6, 9),
}
HELPFUL_TEXTURES = tuple(PALETTES)
DEGENERATE_TEXTURES = ("even_length_runs", "no_runs", "length_1_runs")

AXES = {
    "grid_h": {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "grid_w": {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "run_rows": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..5"},
    "texture": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(unknown)}")


def _draw_int(ctx, overrides, label: str, default_lo: int, default_hi: int,
              valid_lo: int, valid_hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _fill_run(grid, row: int, start: int, length: int, color: int) -> None:
    for column in range(start, start + length):
        grid[row][column] = color


def _available_starts(row: list[int], length: int) -> list[int]:
    width = len(row)
    starts = []
    for start in range(width - length + 1):
        end = start + length
        if any(row[column] != 0 for column in range(start, end)):
            continue
        if start > 0 and row[start - 1] != 0:
            continue
        if end < width and row[end] != 0:
            continue
        starts.append(start)
    return starts


def _run_lengths(grid) -> list[int]:
    result = []
    for row in grid:
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            color = row[column]
            start = column
            while column < len(row) and row[column] == color:
                column += 1
            result.append(column - start)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Require a rectangular ARC grid with at least one odd same-color run."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(type(row) is not list or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid contains a non-ARC cell"]
    lengths = _run_lengths(grid)
    if not lengths:
        return ["no non-zero runs found"]
    for length in lengths:
        if length % 2 == 0:
            return [f"even-length run ({length}) found"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)

    if "texture" in overrides and overrides["texture"] is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
    else:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    if difficulty == "easy":
        h_default, w_default, rows_default = (5, 6), (9, 10), (2, 3)
    elif difficulty == "hard":
        h_default, w_default, rows_default = (7, 8), (12, 13), (4, 5)
    else:
        h_default, w_default, rows_default = (5, 8), (9, 13), (2, 5)

    height = _draw_int(ctx, overrides, "grid_h", *h_default, 3, 12)
    width = _draw_int(ctx, overrides, "grid_w", *w_default, 7, 16)
    row_hi = min(8, height)
    default_row_lo = min(rows_default[0], row_hi)
    default_row_hi = min(rows_default[1], row_hi)
    run_rows = _draw_int(ctx, overrides, "run_rows",
                         default_row_lo, default_row_hi, 1, row_hi)
    color_count = _draw_int(ctx, overrides, "n_distinct_colors", 2, 5, 1, 5)

    rng = ctx.draw_rng("layout")
    grid = full_grid(height, width, 0)
    rows = rng.sample(range(height), run_rows)
    palette = list(PALETTES[texture][:color_count])

    if run_rows >= 2:
        primary_lengths = [1, rng.choice([3, 5])]
        primary_lengths.extend(rng.choice([1, 3, 5]) for _ in range(run_rows - 2))
        rng.shuffle(primary_lengths)
    else:
        primary_lengths = [rng.choice([1, 3, 5])]

    run_number = 0
    for row_index, length in zip(rows, primary_lengths):
        length = min(length, max(value for value in (1, 3, 5) if value <= width))
        starts = _available_starts(grid[row_index], length)
        start = rng.choice(starts)
        color = palette[run_number % len(palette)]
        _fill_run(grid, row_index, start, length, color)
        run_number += 1

        if rng.random() < 0.55:
            second_lengths = [value for value in (1, 3, 5)
                              if _available_starts(grid[row_index], value)]
            if second_lengths:
                second_length = rng.choice(second_lengths)
                second_start = rng.choice(_available_starts(grid[row_index], second_length))
                second_color = palette[run_number % len(palette)]
                _fill_run(grid, row_index, second_start, second_length, second_color)
                run_number += 1

    return grid


def _draw_from_degenerate(name: str):
    height, width = 6, 10
    grid = full_grid(height, width, 0)
    if name == "even_length_runs":
        _fill_run(grid, 1, 1, 4, 3)
        _fill_run(grid, 3, 2, 2, 6)
    elif name == "length_1_runs":
        grid[1][2] = 4
        grid[2][5] = 6
        grid[4][7] = 7
    return grid
