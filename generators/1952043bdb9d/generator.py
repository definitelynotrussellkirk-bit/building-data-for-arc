"""Generator for arc_puzzle_bank_21_next:easy_c02 — Per column, keep only the bottommost non-bg cell.

Rule: for each column, find the lowest row with a non-zero cell;
keep only that cell, zero out the rest.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_columns,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_singletons, all_at_bottom, full_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1952043bdb9d"
VERSION = "3.0.1"  # MAX-DIVERSITY: rule is fully color-agnostic + size-invariant. (1) palette now includes color 1 (was excluded; canonical pairs use 1). (2) widened grid sizes -- hard pushes toward contest scale (up to 12x14) with active-column count + cells-per-column SCALED to grid size so big grids stay dense, not sparse. Each active column still gets >=2 cells so the bottommost-survives rule actually fires.
TASK_ID = "1952043bdb9d"
SUMMARY = (
    "0-bg grid (h~5-7, w~"
    "6-8) where 3-4 "
    "RANDOMLY-CHOSEN "
    "COLUMNS each have 2-3 "
    "NON-BG CELLS at random "
    "rows in various colors "
    "drawn from {2..9}. "
    "Other columns may have "
    "0 or 1 single cells "
    "(at ~50% chance). The "
    "≥3 active columns "
    "ensure the output "
    "differs from input. "
    "Rule (PER-COLUMN, "
    "KEEP ONLY THE "
    "BOTTOMMOST NON-BG "
    "CELL): For EACH "
    "COLUMN c in [0, w-1]"
    ": find the MAXIMUM "
    "ROW r where g[r][c] "
    "≠ 0 (the bottommost "
    "non-bg cell). KEEP "
    "the cell at (r, c) "
    "with its color. "
    "ERASE all OTHER "
    "non-bg cells in "
    "column c (set them "
    "to 0). Columns with "
    "no non-bg cell stay "
    "all 0. Net: each "
    "column collapses to "
    "its bottom-most "
    "painted cell only."
)

INVARIANTS = [
    "≥3 columns have ≥2 non-zero cells (so output differs from input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_singletons", "all_at_bottom", "full_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng by difficulty", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng by difficulty", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_columns":      {"type": "int", "default": "rng 3..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "stacked_columns",
                       "valid": "stacked_columns"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥3 columns have ≥2 non-zero cells (so rule fires)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("all_singletons", "all_at_bottom", "full_columns"):
        return errs
    active_cols = [c for c in range(w)
                   if sum(1 for r in range(h) if grid[r][c] != 0) >= 2]
    if len(active_cols) < 3:
        errs.append(f"expected ≥3 columns with ≥2 non-zero cells, got {len(active_cols)}")
    return errs


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
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]   # color-agnostic rule -> full palette incl. 1
    # active-column count + cells/column scale with grid size so big grids stay
    # dense (every active column has >=2 cells, so the bottommost-survives rule fires).
    n_active = max(3, min(w, rng.randint(w // 2, (3 * w) // 4)))
    cap = max(2, min(h - 1, 4 if h < 9 else 5))
    cols_with_2plus = rng.sample(range(w), n_active)
    for c in cols_with_2plus:
        n = rng.randint(2, cap)
        rs = rng.sample(range(h), n)
        for r in rs:
            g[r][c] = rng.choice(palette)
    other_cols = [c for c in range(w) if c not in cols_with_2plus]
    for c in other_cols:
        if rng.random() < 0.5:
            r = rng.randint(0, h - 1)
            g[r][c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "all_singletons":
        # every column has at most one cell → "bottommost" is that cell, rule is identity
        g[2][1] = 4; g[5][3] = 6; g[3][5] = 3
        return g
    if name == "all_at_bottom":
        # every nonzero already on bottom row → rule is identity
        for c in [1, 3, 5]:
            g[h - 1][c] = (c % 8) + 1
        return g
    if name == "full_columns":
        # active columns completely filled → rule keeps just the bottom cell, dropping h-1 cells
        for c in [1, 4]:
            for r in range(h):
                g[r][c] = (c % 8) + 1
        return g
    return g
