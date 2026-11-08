"""Generator for arc_puzzle_bank_seventh_21_bundle:medium_47_pack_nonempty_columns_left.

Rule: drop all-zero columns; pack remaining columns to the left.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_active_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_active_cols, no_active_cols, all_zero_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a8659653d07"
VERSION = "2.0.1"
TASK_ID = "4a8659653d07"
SUMMARY = (
    "0-bg grid (h~5-8, w~6-9) with several ACTIVE COLUMNS "
    "(2 to w-2) containing 1-h//2 cells in some non-bg "
    "color (each active column may have its own color). "
    "Other columns are entirely 0. Rule: drop every ALL-"
    "ZERO column. PACK the remaining (active) columns to "
    "the LEFT in their original left-to-right order. "
    "Output: h × N_active grid containing just the "
    "active columns, no gaps."
)

INVARIANTS = [
    "background is 0",
    "≥2 non-empty cols + ≥1 all-zero col gap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_active_cols", "no_active_cols", "all_zero_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_active_cols":  {"type": "int", "default": "rng 2..w-2", "valid": "2..10"},
    "palette_size":   {"type": "int", "default": "rng 1..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "col_sparse", "valid": "col_sparse"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 6, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_active = rng.randint(2, max(2, w - 2))
    active_cols = sorted(rng.sample(range(w), n_active))
    for c in active_cols:
        n_cells = rng.randint(1, max(1, h // 2))
        rows = rng.sample(range(h), n_cells)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r in rows:
            g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify pack-columns-left input invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    problems = []
    active_cols = [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]
    zero_cols = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    if len(active_cols) < 2:
        problems.append(f"expected >=2 active columns, found {len(active_cols)}")
    if not zero_cols:
        problems.append("no all-zero column gap found")
    return problems


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "all_active_cols":
        # every column has nonzero cells → rule is identity (no gaps to pack)
        for c in range(w):
            g[c % h][c] = ((c % 7) + 1)
        return g
    if name == "no_active_cols":
        # only one active column → predicate "≥2 nonempty cols" fails
        for r in range(h):
            g[r][3] = 5
        return g
    if name == "all_zero_grid":
        # entirely zero → output is an empty (h × 0) grid
        return g
    return g
