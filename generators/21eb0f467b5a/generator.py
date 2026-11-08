"""Generator for arc_additional_puzzles_21_set14_bundle:E97.

The canonical rule completes every exactly-two-cell horizontal or vertical
color pair and preserves every other color at its original cells.  Ordinary
scenes expose one nontrivial aligned pair and one singleton.  All declared
controls are strict and observable; degenerate textures remain explicit only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "21eb0f467b5a"
VERSION = "2.2.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "Complete the inclusive segment between each color's exactly two aligned "
    "cells; preserve non-pair, diagonal-pair and singleton colors."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "at least one exactly-two-cell aligned color pair with two or more blanks between endpoints",
    "one singleton of another color outside that segment",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pair", "no_alignment", "adjacent_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "difficulty band", "valid": "4..10"},
    "grid_w": {"type": "int", "default": "difficulty band", "valid": "6..14"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "alignment": {"type": "str", "default": "rng row|col", "valid": "row|col"},
    "palette_size": {"type": "int", "default": "2", "valid": "2"},
    "position_bias": {"type": "str", "default": "aligned_pair_plus_singleton", "valid": "aligned_pair_plus_singleton"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_PALETTES = {
    "default": (2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 3, 4, 6, 9),
    "cool": (1, 5, 7, 8),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
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


def _difficulty_bounds(difficulty):
    if difficulty == "easy":
        return (5, 7), (8, 10)
    if difficulty == "medium":
        return (6, 9), (9, 12)
    if difficulty == "hard":
        return (8, 10), (12, 14)
    if difficulty is None:
        return (5, 10), (8, 14)
    raise ValueError("difficulty must be easy, medium, hard or None")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if any(value is not None for name, value in overrides.items() if name != "texture"):
            raise ValueError("degenerate textures do not support additional overrides")
        return _draw_from_degenerate(texture)

    settings = dict(overrides)
    if texture is not None:
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture: {texture}")
        if settings.get("palette_kind") not in (None, texture):
            raise ValueError("texture and palette_kind must agree")
        settings["palette_kind"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=settings)
    (h_lo, h_hi), (w_lo, w_hi) = _difficulty_bounds(difficulty)
    h = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    w = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    alignment = ctx.draw_choice("alignment", ("row", "col"))
    profile = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    ctx.draw_int_strict("palette_size", 2, 2)
    ctx.draw_int_strict("n_distinct_colors", 2, 2)
    ctx.draw_choice("position_bias", ("aligned_pair_plus_singleton",))
    ctx.draw_choice("density", ("sparse",))

    rng = ctx.draw_rng("layout")
    palette = rng.sample(list(_PALETTES[profile]), 2)
    grid = full_grid(h, w, 0)
    if alignment == "row":
        row = rng.randrange(h)
        left = rng.randrange(w - 3)
        right = rng.randrange(left + 3, w)
        endpoints = ((row, left), (row, right))
        segment = {(row, col) for col in range(left, right + 1)}
    else:
        col = rng.randrange(w)
        top = rng.randrange(h - 3)
        bottom = rng.randrange(top + 3, h)
        endpoints = ((top, col), (bottom, col))
        segment = {(row, col) for row in range(top, bottom + 1)}
    for row, col in endpoints:
        grid[row][col] = palette[0]

    candidates = [(row, col) for row in range(h) for col in range(w)
                  if (row, col) not in segment]
    if alignment == "row":
        off_line = [cell for cell in candidates if cell[0] != endpoints[0][0]]
    else:
        off_line = [cell for cell in candidates if cell[1] != endpoints[0][1]]
    row, col = rng.choice(off_line or candidates)
    grid[row][col] = palette[1]
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be exact integers in 0..9"]
    cells = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                cells.setdefault(color, []).append((row, col))
    for points in cells.values():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2 and abs(c1 - c2) >= 3:
            return []
        if c1 == c2 and abs(r1 - r2) >= 3:
            return []
    return ["no aligned exactly-two-cell pair with at least two blank cells"]


def _draw_from_degenerate(name):
    grid = full_grid(6, 9, 0)
    if name == "no_pair":
        grid[2][4] = 6
    elif name == "no_alignment":
        grid[1][1] = 4
        grid[3][5] = 4
        grid[5][8] = 6
    elif name == "adjacent_pair":
        grid[2][3] = 4
        grid[2][4] = 4
        grid[4][7] = 6
    else:
        raise ValueError(f"unknown degenerate texture: {name}")
    return grid
