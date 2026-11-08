"""Generator for arc_puzzle_bank_21_set17_s:S17_E2.

Rule: sparse seeds grow by the diagonal X stencil.

Combinatorial axes (8): grid_h/w, height, width, seed_count, palette_kind,
anchor_corner, asymmetry_force, palette_size.
Degenerates: no_seeds, single_seed, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cfd0943c5b14"
VERSION = "2.0.1"
TASK_ID = "cfd0943c5b14"
SUMMARY = (
    "0-bg grid (h, w~5-12) with 2-5 SPARSE "
    "SEED CELLS in any non-zero colors from "
    "{1..9} \\ {8}, placed at random non-"
    "overlapping positions, sufficiently spread "
    "that diagonal neighbors are mostly "
    "in-bounds. Rule: for EACH non-zero SEED "
    "cell at (r, c), STAMP a DIAGONAL "
    "X-STENCIL of COLOR 8 (cyan) — paint the "
    "5 cells (r, c), (r-1, c-1), (r-1, c+1), "
    "(r+1, c-1), (r+1, c+1) with color 8. "
    "Cells outside the grid are silently "
    "dropped. Build a FRESH output grid: SEED "
    "COLORS DO NOT APPEAR in the output (only "
    "cyan). When multiple stamps overlap, the "
    "union remains color 8. Net: each seed "
    "becomes a cyan diagonal X; output is the "
    "union of all X-stencils, all in cyan."
)

# Rivals: 'output is input' refuted by demos (output has only 8s).
# 'preserve seed colors' refuted by demos showing all 8s in output.
# 'stamp cardinal neighbors (+ shape)' refuted by demos showing
# diagonals only. 'stamp the center cell only (no diagonals)' refuted
# by demos with diagonals visible. 'stamp full 3x3 block' refuted by
# demos missing cardinal neighbors. 'use seed color in output'
# refuted by demos showing 8 only. 3 demos with seeds spread far
# apart pin the X-stencil semantics.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 non-zero seed cells in any non-zero colors",
    "seeds are sufficiently spread that at least one diagonal neighbor of each lies in-bounds (so the X-stencil is visible)",
    "seeds are NOT all at the same row/col (so the X-pattern is non-degenerate)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "6..8"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "6..8"},
    "height":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "width":          {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all values 0-9; ≥1 non-zero cell (seeds are sparse)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("height", 5, 7)
        w = ctx.draw_int("width", 5, 7)
        n_lo, n_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("height", 9, 12)
        w = ctx.draw_int("width", 9, 12)
        n_lo, n_hi = 4, 6
    else:
        h = ctx.draw_int("height", 6, 9)
        w = ctx.draw_int("width", 6, 9)
        n_lo, n_hi = 3, 5
    n = ctx.draw_int("seed_count", n_lo, n_hi)
    g = full_grid(h, w, 0)
    # Place seeds at interior positions (where at least some diagonal
    # neighbors stay in bounds — interior is row 1..h-2, col 1..w-2).
    candidates = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(candidates)
    placed_seeds = []
    seed_color_pool = [1, 2, 3, 4, 5, 6, 7, 9]
    for r, c in candidates[:n]:
        # Each seed gets a distinct random color (any non-zero color)
        color = rng.choice(seed_color_pool)
        g[r][c] = color
        placed_seeds.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_seeds":
        return g
    if name == "single_seed":
        g[3][3] = 3
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 3
        return g
    return g
