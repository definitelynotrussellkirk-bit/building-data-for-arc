"""Generator for 4b:m27 — place cross at bbox center.

Rule: replace each blob with a 5-cell plus-cross at its bbox center.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, single_cell_blobs, blob_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "306332da48b4"
VERSION = "1.1.1"
TASK_ID = "306332da48b4"
SUMMARY = "2-3 distinct-color blobs of size ≥3 with bbox centers spaced apart."

INVARIANTS = [
    "background is 0",
    "blobs of size >= 3, bbox centers at distinct positions",
    "blobs not on grid border so cross fits in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "single_cell_blobs", "blob_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "interior_blobs",
                       "valid": "interior_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """≥1 non-zero blob; grid is nonempty and rectangular."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    has_cell = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not has_cell:
        errs.append("no non-zero blob cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    for r in range(h):
        used.add((r, 0)); used.add((r, w - 1))
    for c in range(w):
        used.add((0, c)); used.add((h - 1, c))
    for color in palette:
        cells = grow_blob(rng, h, w, used, rng.randint(3, 4), max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no blobs to convert into crosses
        return g
    if name == "single_cell_blobs":
        # 1-cell blobs → bbox center == the cell, cross extends 1 in each direction
        g[3][3] = 4
        g[5][7] = 6
        return g
    if name == "blob_at_corner":
        # blob touching corner → cross at bbox center extends out of bounds
        g[0][0] = 4; g[0][1] = 4; g[1][0] = 4
        return g
    return g
