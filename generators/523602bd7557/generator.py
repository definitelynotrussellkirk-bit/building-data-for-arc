"""Generator for arc_puzzle_bank_fifth21:M31 — sweep right to 9-wall.

Rule: a vertical 9-wall on the right side. Each blob extends its
cells rightward (per-row) until they hit the wall.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_wall, no_blobs, blob_right_of_wall.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "523602bd7557"
VERSION = "1.1.1"
TASK_ID = "523602bd7557"
SUMMARY = "Vertical 9-wall on right + 2-3 distinct-color blobs to its left."

INVARIANTS = [
    "background is 0",
    "exactly one full vertical 9-line at col w-3",
    "all non-9 blobs are entirely left of the wall",
    "blobs occupy disjoint row ranges (so sweeps don't collide)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_wall", "no_blobs", "blob_right_of_wall")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "wall_plus_left_blobs",
                       "valid": "wall_plus_left_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 full-height color-9 wall column; >=1 non-{0,9} blob cell left of it."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    wall_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(wall_cols) != 1:
        errs.append(f"expected exactly 1 full-height color-9 wall column, found {len(wall_cols)}")
    else:
        wc = wall_cols[0]
        has_blob = any(grid[r][c] not in (0, 9) for r in range(h) for c in range(wc))
        if not has_blob:
            errs.append("no non-{0,9} blob cells left of the wall")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n_blobs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_blobs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_blobs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    wall_c = w - 3
    for r in range(h):
        g[r][wall_c] = 9
    used = {(r, wall_c) for r in range(h)}
    for r in range(h):
        for c in range(wall_c, w):
            used.add((r, c))
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8], n)
    placed_rows = set()
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=20)
            if cells is None:
                continue
            rs = set(r for r, _ in cells)
            if rs & placed_rows:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            placed_rows |= rs
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_wall":
        # blobs but no 9-wall → no stop point, sweep extends to grid edge
        g[2][2] = 4; g[2][3] = 4
        g[5][1] = 6
        return g
    if name == "no_blobs":
        # wall only → nothing to sweep
        for r in range(h): g[r][w - 3] = 9
        return g
    if name == "blob_right_of_wall":
        # blob is on the wrong side of the wall → sweep direction undefined
        for r in range(h): g[r][3] = 9
        g[2][6] = 4; g[2][7] = 4
        return g
    return g
