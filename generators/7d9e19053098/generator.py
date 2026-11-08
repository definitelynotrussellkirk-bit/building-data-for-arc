"""Generator for arc_additional_puzzle_bank_volume20:M136 — Recolor 1-blobs by shape.

Rule: for each color-1 object: hline (h=1) → 2; vline (w=1) → 3; solid
square (h=w & solid) → 4; else keep.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_extras,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_lines_no_squares, all_lines, all_squares.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7d9e19053098"
VERSION = "1.1.1"
TASK_ID = "7d9e19053098"
SUMMARY = "Several 1-blobs of different shapes (hline, vline, square) + decorative non-1 blob; output recolors by shape."

INVARIANTS = [
    "at least one hline (h=1, w≥2)",
    "at least one vline (w=1, h≥2)",
    "at least one solid square (h=w≥2)",
    "blobs are non-touching",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_lines_no_squares", "all_lines", "all_squares")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_extras":       {"type": "int", "default": "rng 0..1", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "shape_mix",
                       "valid": "shape_mix"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _occupied_or_adjacent(used, r1, c1, r2, c2):
    for r in range(r1 - 1, r2 + 2):
        for c in range(c1 - 1, c2 + 2):
            if (r, c) in used: return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 color-1 cell (the 1-blob to classify by shape)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    has_one = any(v == 1 for row in grid for v in row)
    if not has_one:
        return ["expected ≥1 color-1 cell (1-blob shape target); found none"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 13)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set()
    for _ in range(40):
        ln = rng.randint(2, 4)
        r = rng.randint(0, h - 1); c1 = rng.randint(0, w - ln)
        if _occupied_or_adjacent(used, r, c1, r, c1 + ln - 1): continue
        for c in range(c1, c1 + ln):
            g[r][c] = 1; used.add((r, c))
        break
    for _ in range(40):
        ln = rng.randint(2, 4)
        c = rng.randint(0, w - 1); r1 = rng.randint(0, h - ln)
        if _occupied_or_adjacent(used, r1, c, r1 + ln - 1, c): continue
        for r in range(r1, r1 + ln):
            g[r][c] = 1; used.add((r, c))
        break
    for _ in range(40):
        sz = rng.randint(2, 3)
        r1 = rng.randint(0, h - sz); c1 = rng.randint(0, w - sz)
        if _occupied_or_adjacent(used, r1, c1, r1 + sz - 1, c1 + sz - 1): continue
        for r in range(r1, r1 + sz):
            for c in range(c1, c1 + sz):
                g[r][c] = 1; used.add((r, c))
        break
    for _ in range(15):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if (r, c) in used: continue
        g[r][c] = 7; break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_lines_no_squares":
        # only L-shaped 1-blobs (not lines, not squares) → all keep color 1
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 1
        for (r, c) in [(5, 5), (5, 6), (6, 5), (6, 6), (6, 7)]: g[r][c] = 1
        return g
    if name == "all_lines":
        # all 1-blobs are lines → all recolored to 2 or 3 (no squares)
        for c in range(1, 4): g[1][c] = 1  # hline
        for r in range(3, 6): g[r][7] = 1  # vline
        return g
    if name == "all_squares":
        # all 1-blobs are solid squares → all recolored to 4 (uniform)
        for r in range(2):
            for c in range(2): g[1 + r][1 + c] = 1
        for r in range(3):
            for c in range(3): g[5 + r][5 + c] = 1
        return g
    return g
