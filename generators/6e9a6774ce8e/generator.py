"""Generator for arc_puzzle_bank_21_set6:easy_f01.

Rule: center-pack the nonzero values in each row, preserving row order.

Combinatorial axes (8): grid_h, grid_w, palette_kind, active_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_already_centered, all_blank, single_full_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6e9a6774ce8e"
VERSION = "1.1.1"
TASK_ID = "6e9a6774ce8e"
SUMMARY = "Center-pack the nonzero values in each row, preserving row order."

INVARIANTS = [
    "background is 0",
    "rows are transformed independently",
    "nonzero values keep their left-to-right order",
    "packed values are centered within the row",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_already_centered", "all_blank", "single_full_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "active_rows":    {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_uncentered",
                       "valid": "row_uncentered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 non-zero cell; skip degenerate textures."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero == 0:
        errs.append("no non-zero cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
        active = min(ctx.draw_int("active_rows", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
        active = min(ctx.draw_int("active_rows", 4, 5), h)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        active = min(ctx.draw_int("active_rows", 3, 5), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), active)
    forced = rng.choice(rows)
    for r in rows:
        k = rng.randint(1, min(4, w))
        cols = sorted(rng.sample(range(w), k))
        if r == forced:
            start = (w - k) // 2
            centered = list(range(start, start + k))
            if cols == centered:
                cols = sorted(rng.sample([c for c in range(w) if c not in centered], k))
        for c, color in zip(cols, rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k)):
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "all_already_centered":
        # all active rows are already centered → rule is identity, output equals input
        # Each row has 3 contiguous cells centered in the 9-wide row at cols 3,4,5
        for r in [1, 3, 5]:
            for c in [3, 4, 5]:
                g[r][c] = (r % 8) + 1
        return g
    if name == "all_blank":
        # blank grid → no nonzeros to pack, rule is identity
        return g
    if name == "single_full_row":
        # one row completely filled → already spans the whole width, "center-pack" is identity
        for c in range(w):
            g[2][c] = (c % 8) + 1
        return g
    return g
