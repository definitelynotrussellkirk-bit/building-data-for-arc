"""Generator for arc_puzzle_bank_21_set13_bundle:medium_m03 — sort objects into gallery.

Rule: extract each blob's bbox-cropped subgrid, sort by bbox height
(descending), and pack horizontally with a 1-col gap separator.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, single_blob, tied_heights.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "baec9a7715e7"
VERSION = "1.2.1"  # 1.2.0->1.2.1: add self_check. 1.1.0->1.2.0: 3-5 blobs of varied sizes (3..8 cells, often
# non-square bboxes) instead of fixed 3 blobs sized 3/4/5 -> far more output
# width/height variety (out_shapes 4 -> higher). Sort is deterministic
# (rows,cols,string) so distinct heights are no longer required.
TASK_ID = "baec9a7715e7"
SUMMARY = "3-5 distinct-color blobs of varied sizes/shapes (incl non-square bboxes)."

INVARIANTS = [
    "background is 0",
    "3-5 blobs of distinct colors",
    "blobs don't overlap or touch (isolated 4-connected components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "single_blob", "tied_heights")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "varied_blobs",
                       "valid": "varied_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; 2+ distinct nonzero colors present as separate blobs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        return errs  # degenerate no_blobs
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct blob colors, got {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        n_blobs = ctx.draw_int("n_blobs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 14, 16)
        n_blobs = ctx.draw_int("n_blobs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        n_blobs = ctx.draw_int("n_blobs", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_blobs)
    used: set[tuple[int, int]] = set()
    placed = 0
    for color in palette:
        size = rng.randint(3, 8)
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, size, max_attempts=20)
            if cells is None:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            placed += 1
            break
    if placed == 0:
        # guarantee at least one object
        g[1][1] = palette[0]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no blobs to sort by height
        return g
    if name == "single_blob":
        # 1 blob → trivial, no sorting contrast
        for r, c in [(2, 2), (3, 2), (3, 3)]: g[r][c] = 4
        return g
    if name == "tied_heights":
        # 2 blobs share bbox height → "strictly distinct" precondition fails
        for r, c in [(1, 1), (2, 1), (3, 1)]: g[r][c] = 4  # height 3
        for r, c in [(1, 5), (2, 5), (3, 5)]: g[r][c] = 6  # height 3 (tied)
        for r, c in [(5, 1)]: g[r][c] = 7  # height 1
        return g
    return g
