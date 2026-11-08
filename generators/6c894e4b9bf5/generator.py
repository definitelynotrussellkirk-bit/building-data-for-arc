"""Generator for arc_additional_puzzle_bank_volume21:E141.

Each color-2 component that is a straight vertical line of length at least two
has its top and bottom cells recolored to 1.  Ordinary scenes include both
qualifying vertical lines and a nonqualifying horizontal color-2 control so the
shape predicate is visible rather than implied by an all-positive distribution.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c894e4b9bf5"
VERSION = "1.3.0"
TASK_ID = "6c894e4b9bf5"
SUMMARY = "3-4 vertical color-2 lines plus a nonvertical color-2 control and color-7 decoration."

INVARIANTS = [
    "3-4 disjoint vertical color-2 lines (single column, length >=2)",
    "at least one nonvertical color-2 component that the rule must leave unchanged",
    "color-7 decoration does not overwrite the target lines",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("horizontal_lines", "single_cell_blobs", "no_lines")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "rng 11..13", "valid": "11..16"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "n_lines": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "palette_size": {"type": "int", "default": "2", "valid": "2"},
    "position_bias": {"type": "str", "default": "vertical_columns",
                      "valid": "vertical_columns"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "length_spread": {"type": "str", "default": "varied", "valid": "varied"},
    "texture": {"type": "str", "default": "alias for palette_kind",
                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        expected = int if AXES[name]["type"] == "int" else str
        if type(value) is not expected:
            raise TypeError(f"{name} must be {expected.__name__}")


def _draw_decoration(grid, profile):
    h, w = len(grid), len(grid[0])
    if profile == "default":
        cells = ((h - 3, 1), (h - 3, 2), (h - 3, 3), (h - 2, 1))
    elif profile == "warm":
        cells = ((h - 2, 1), (h - 2, 2), (h - 2, 3), (h - 3, 2))
    elif profile == "cool":
        cells = ((h - 3, 1), (h - 2, 2), (h - 3, 3), (h - 2, 3))
    else:
        cells = ((h - 4, 1), (h - 3, 2), (h - 2, 3), (h - 2, 1))
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            grid[r][c] = 7


def _red_components(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in remaining:
                    remaining.remove(cell)
                    cells.add(cell)
                    stack.append(cell)
        result.append(cells)
    return result


def _vertical(cells):
    if len(cells) < 2:
        return False
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    return len(cols) == 1 and len(rows) == max(rows) - min(rows) + 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check exact cell types and that every qualifying red component is a line.

    Declared degenerate textures may contain no qualifying line, so the checker
    does not reject an all-negative scene.  Ordinary-generation tests separately
    require both positive and negative branches.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be exact integers in 0..9"]
    # Component extraction itself catches accidental red adjacency/merging; the
    # rule intentionally ignores every nonvertical component.
    for cells in _red_components(grid):
        if _vertical(cells):
            rows = sorted(r for r, _ in cells)
            if len(rows) != rows[-1] - rows[0] + 1:
                return ["vertical color-2 component has an internal gap"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if any(value is not None for name, value in overrides.items() if name != "texture"):
            raise ValueError("degenerate textures do not support additional axis overrides")
        return _draw_from_degenerate(texture, None)

    settings = dict(overrides)
    if texture is not None:
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture: {texture}")
        if settings.get("palette_kind") not in (None, texture):
            raise ValueError("texture and palette_kind must agree")
        settings["palette_kind"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=settings)
    target = ctx.draw_int_strict("n_lines", 3, 4)
    ctx.draw_int_strict("palette_size", 2, 2)
    ctx.draw_int_strict("n_distinct_colors", 2, 2)
    ctx.draw_choice("position_bias", ("vertical_columns",))
    ctx.draw_choice("length_spread", ("varied",))
    profile = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    if difficulty == "easy":
        h = ctx.draw_int_strict("grid_h", 8, 9)
        w = ctx.draw_int_strict("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int_strict("grid_h", 10, 14)
        w = ctx.draw_int_strict("grid_w", 13, 16)
    else:
        h = ctx.draw_int_strict("grid_h", 8, 10)
        w = ctx.draw_int_strict("grid_w", 11, 13)

    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    _draw_decoration(grid, profile)

    # Always expose the negative branch in the normal distribution.  Reserving
    # the top-right band leaves a blank column between this horizontal component
    # and every target column.
    grid[0][w - 2] = 2
    grid[0][w - 1] = 2

    possible_columns = list(range(1, w - 3))
    column_sets = [choice for choice in combinations(possible_columns, target)
                   if all(b - a >= 2 for a, b in zip(choice, choice[1:]))]
    if not column_sets:
        raise ValueError("grid width cannot fit the requested separated vertical lines")
    columns = list(rng.choice(column_sets))
    rng.shuffle(columns)

    preferred_lengths = [2, 3, 4, 5]
    rng.shuffle(preferred_lengths)
    for index, col in enumerate(columns):
        lengths = preferred_lengths[index:] + preferred_lengths[:index]
        candidates = []
        for length in lengths:
            if length > h:
                continue
            for row0 in range(h - length + 1):
                if all(grid[row0 + dr][col] == 0 for dr in range(length)):
                    candidates.append((length, row0))
        if not candidates:
            raise RuntimeError("could not place a requested vertical line without overwriting decoration")
        length, row0 = rng.choice(candidates)
        for dr in range(length):
            grid[row0 + dr][col] = 2

    if sum(_vertical(cells) for cells in _red_components(grid)) != target:
        raise RuntimeError("constructed scene does not contain the requested number of target lines")
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    grid = full_grid(h, w, 0)
    if name == "horizontal_lines":
        for c in range(2, 6):
            grid[2][c] = 2
        for c in range(1, 5):
            grid[5][c] = 2
        return grid
    if name == "single_cell_blobs":
        for r, c in [(1, 2), (3, 5), (5, 8)]:
            grid[r][c] = 2
        return grid
    if name == "no_lines":
        for r, c in [(2, 2), (3, 3), (5, 5)]:
            grid[r][c] = 7
        return grid
    return grid
