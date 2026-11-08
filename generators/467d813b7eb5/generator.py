"""Generator for arc_puzzle_bank_21_set24_s:S24_E2 — solid components reduce to deepest onion-layer cells.

Rule: each solid rectangular component is reduced to its deepest
onion-layer cells (cells maximally far from the border of the
component).

Combinatorial axes (8): grid_h, grid_w, palette_kind, object_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, hollow_components, single_layer.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "467d813b7eb5"
VERSION = "1.1.1"
TASK_ID = "467d813b7eb5"
SUMMARY = "Solid components reduce to their deepest onion-layer cells."

INVARIANTS = [
    "background is 0",
    "objects are separated solid rectangles",
    "each object has at least one deepest cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "hollow_components", "single_layer")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "rng 13..17", "valid": "8..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "object_count":   {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "= object_count", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "scattered_solid_rects",
                       "valid": "scattered_solid_rects"},
    "n_distinct_colors": {"type": "int", "default": "= object_count", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(grid, r0, c0, rh, rw):
    h, w = len(grid), len(grid[0])
    if r0 < 0 or c0 < 0 or r0 + rh > h or c0 + rw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
            if grid[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
        count = ctx.draw_int("object_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 18)
        w = ctx.draw_int("grid_w", 17, 21)
        count = ctx.draw_int("object_count", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        count = ctx.draw_int("object_count", 2, 3)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], count)
    placed = 0
    for color in colors:
        for _ in range(80):
            size = rng.randint(3, 6)
            rh = size + rng.randint(0, 1)
            rw = size + rng.randint(0, 2)
            r0 = rng.randint(0, h - rh)
            c0 = rng.randint(0, w - rw)
            if not _free(grid, r0, c0, rh, rw):
                continue
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + rw):
                    grid[r][c] = color
            placed += 1
            break
        if placed >= count:
            break
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 13, 15
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no component to onion-peel.
        return g
    if name == "hollow_components":
        # Frames (rectangles with hollow interiors) — the rule's
        # interior-of-solid-rect logic doesn't fit hollow shapes.
        for c in range(2, 7):
            g[2][c] = 4; g[6][c] = 4
        for r in range(2, 7):
            g[r][2] = 4; g[r][6] = 4
        for c in range(9, 13):
            g[3][c] = 6; g[7][c] = 6
        for r in range(3, 8):
            g[r][9] = 6; g[r][12] = 6
        return g
    if name == "single_layer":
        # 1x1 components — the deepest layer is the cell itself, so
        # the rule trivially returns the input unchanged.
        g[2][3] = 4; g[5][7] = 6; g[8][11] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 non-zero solid rect object with at least 3x3 extent."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    # Find bounding boxes of each color
    colors = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                colors.add(grid[r][c])
    if not colors:
        errors.append("no non-zero objects found")
        return errors
    # At least one object with bbox >=3 wide and >=3 tall (needed for onion peeling)
    found_deep = False
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if not cells:
            continue
        rs = [r for r, c in cells]; cs = [c for r, c in cells]
        if (max(rs) - min(rs) + 1 >= 3) and (max(cs) - min(cs) + 1 >= 3):
            found_deep = True
            break
    if not found_deep:
        errors.append("no object has a bbox of at least 3x3 (needed for onion-layer peeling)")
    return errors
