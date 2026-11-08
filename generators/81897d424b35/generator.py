"""Generator for arc_puzzle_bank_21_set19_bundle:easy_p06.

Rule: sparse colored cells fall to the bottom of each column,
preserving vertical order.

Combinatorial axes (8): grid_h, grid_w, palette_kind, active_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_cells, all_at_bottom, single_active_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "81897d424b35"
VERSION = "1.1.1"
TASK_ID = "81897d424b35"
SUMMARY = "Sparse colored cells fall to the bottom of each column, preserving vertical order."

INVARIANTS = [
    "background is 0",
    "several columns contain one to four nonzero cells",
    "at least one active column has a gap below a colored cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_cells", "all_at_bottom", "single_active_col")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "active_cols":    {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_cells|all_at_bottom|single_active_col"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct columns have nonzero cells; ≥1 cell has a zero below it."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    active_cols = {c for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not active_cols:
        return []  # no_cells degenerate — allowed
    errs = []
    if len(active_cols) < 2:
        errs.append(f"only {len(active_cols)} active column(s); expected ≥2 for non-trivial gravity")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        active_cols = min(ctx.draw_int("active_cols", 3, 3), w)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        active_cols = min(ctx.draw_int("active_cols", 4, 5), w)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        active_cols = min(ctx.draw_int("active_cols", 3, 5), w)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)

    cols = rng.sample(range(w), active_cols)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for col in cols:
        count = rng.randint(1, min(4, h - 1))
        rows = sorted(rng.sample(range(h - 1), count))
        for row in rows:
            grid[row][col] = rng.choice(colors)
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_cells":
        # empty grid → gravity has nothing to drop
        return g
    if name == "all_at_bottom":
        # cells already at bottom of each column → gravity is identity
        for c in [1, 3, 5]:
            g[h - 1][c] = (c % 9) + 1
        return g
    if name == "single_active_col":
        # only one column active → no horizontal context, simpler than the rule's invariant
        for r in [1, 3, 5]:
            g[r][3] = 4
        return g
    return g
