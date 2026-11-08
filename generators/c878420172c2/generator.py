"""Generator for H9 — intersect two shapes after top-left normalization.

Regular draws use two distinct connected polyominoes of equal size.  Each is
normalized to a 3×3 local frame containing (0,0), so their normalized sets have
a non-empty intersection while remaining structurally different.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c878420172c2"
VERSION = "1.3.0"
TASK_ID = "c878420172c2"
SUMMARY = (
    "Two separate connected shapes in colors 2 and 3 are translated to a "
    "common top-left origin; output paints their normalized intersection in 8."
)

INVARIANTS = [
    "exactly one four-connected blob of color 2 and one of color 3",
    "the normalized shapes are distinct",
    "their normalized cell sets share at least one position",
]

DEGENERATE_TEXTURES = ("identical_shapes", "disjoint_shapes", "single_color")
TEXTURES = ("default",) + DEGENERATE_TEXTURES

AXES = {
    "grid_h": {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "n_shape": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "texture": {"type": "str", "default": "default", "valid": "|".join(TEXTURES)},
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


def _connected(cells) -> bool:
    cells = set(cells)
    if not cells:
        return False
    first = next(iter(cells))
    seen = {first}
    stack = [first]
    while stack:
        row, column = stack.pop()
        for neighbor in ((row - 1, column), (row + 1, column),
                         (row, column - 1), (row, column + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _normalize(cells):
    cells = set(cells)
    row0 = min(row for row, _ in cells)
    column0 = min(column for _, column in cells)
    return frozenset((row - row0, column - column0) for row, column in cells)


@lru_cache(maxsize=None)
def _shape_bank(size: int):
    positions = [(row, column) for row in range(3) for column in range(3)]
    bank = []
    for combo in combinations(positions, size):
        cells = frozenset(combo)
        if (0, 0) in cells and _connected(cells):
            bank.append(cells)
    if not bank:
        raise ValueError(f"no connected shape bank for size {size}")
    return tuple(bank)


def _bbox_size(cells) -> tuple[int, int]:
    return (max(row for row, _ in cells) + 1,
            max(column for _, column in cells) + 1)


def _choose_shapes(rng, size: int):
    bank = _shape_bank(size)
    first = rng.choice(bank)
    alternatives = [shape for shape in bank if shape != first and shape & first]
    second = rng.choice(alternatives)
    return first, second


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = (ctx.draw_choice("texture", TEXTURES)
               if "texture" in overrides and overrides["texture"] is not None
               else "default")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    if difficulty == "easy":
        h_default, w_default, n_default = (8, 9), (9, 10), (2, 3)
    elif difficulty == "hard":
        h_default, w_default, n_default = (9, 10), (11, 12), (5, 6)
    else:
        h_default, w_default, n_default = (8, 10), (9, 12), (3, 5)

    height = _draw_int(ctx, overrides, "grid_h", *h_default, 7, 14)
    width = _draw_int(ctx, overrides, "grid_w", *w_default, 8, 16)
    shape_size = _draw_int(ctx, overrides, "n_shape", *n_default, 2, 6)
    rng = ctx.draw_rng("layout")
    shape2, shape3 = _choose_shapes(rng, shape_size)
    h2, w2 = _bbox_size(shape2)
    h3, w3 = _bbox_size(shape3)

    top_row_max = max(0, height // 2 - h2)
    left_col_max = max(0, width // 2 - w2)
    row2 = rng.randint(0, top_row_max)
    col2 = rng.randint(0, left_col_max)
    row3_min = min(height - h3, (height + 1) // 2)
    col3_min = min(width - w3, (width + 1) // 2)
    row3 = rng.randint(row3_min, height - h3)
    col3 = rng.randint(col3_min, width - w3)

    grid = full_grid(height, width, 0)
    for row, column in shape2:
        grid[row2 + row][col2 + column] = 2
    for row, column in shape3:
        grid[row3 + row][col3 + column] = 3
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(type(row) is not list or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid contains a non-ARC cell"]

    messages = []
    cells = {
        color: {(row, column) for row, values in enumerate(grid)
                for column, value in enumerate(values) if value == color}
        for color in (2, 3)
    }
    for color in (2, 3):
        if not cells[color]:
            messages.append(f"no color-{color} cells found")
        elif not _connected(cells[color]):
            messages.append(f"color-{color} cells are not one four-connected blob")
    if cells[2] and cells[3]:
        normalized2 = _normalize(cells[2])
        normalized3 = _normalize(cells[3])
        if normalized2 == normalized3:
            messages.append("normalized color-2 and color-3 shapes are identical")
        if not (normalized2 & normalized3):
            messages.append("normalized color-2 and color-3 shapes have no common positions")
    return messages


def _draw_from_degenerate(name: str):
    height, width = 9, 10
    grid = full_grid(height, width, 0)
    if name == "identical_shapes":
        for row, column in ((1, 1), (1, 2), (2, 1), (2, 2)):
            grid[row][column] = 2
        for row, column in ((5, 6), (5, 7), (6, 6), (6, 7)):
            grid[row][column] = 3
    elif name == "disjoint_shapes":
        for row, column in ((1, 1), (1, 2), (1, 3)):
            grid[row][column] = 2
        for row, column in ((5, 6), (6, 6), (7, 6)):
            grid[row][column] = 3
    elif name == "single_color":
        for row, column in ((1, 1), (1, 2), (2, 1)):
            grid[row][column] = 2
    return grid
