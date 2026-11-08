"""Generator for v0_original:easy_05.

Rule: each non-zero seed cell paints a down-right diagonal of its
color until the grid edge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_bottom_right, two_seeds_same_diag.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f20defd6ea3c"
VERSION = "2.2.0"  # add diagonal-separation guard + executable self_check
TASK_ID = "f20defd6ea3c"
SUMMARY = (
    "0-bg grid (h~4-6, w~"
    "5-7) with 1-3 NON-"
    "ZERO SEED CELLS in "
    "DISTINCT non-0 "
    "colors from {1..9}. "
    "Each seed is a "
    "single cell at a "
    "random interior "
    "position (not in the "
    "last row or column "
    "so there's room for "
    "the diagonal to "
    "extend). Rule (EACH "
    "SEED PAINTS A DOWN-"
    "RIGHT DIAGONAL OF "
    "ITS COLOR UNTIL THE "
    "GRID EDGE): For "
    "EACH SEED at (r, c) "
    "with color C: PAINT "
    "cells (r+1, c+1), "
    "(r+2, c+2), ..., "
    "(r+k, c+k) with "
    "color C until r+k "
    "or c+k goes out of "
    "bounds. The seed "
    "itself stays at C. "
    "Net: each seed "
    "emits a down-right "
    "diagonal ray of its "
    "color reaching the "
    "bottom or right edge."
)

INVARIANTS = [
    "background is 0",
    "1-3 single-cell seeds in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_bottom_right", "two_seeds_same_diag")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..11"},
    "grid_w":         {"type": "int", "default": "rng 5..7", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 5, 7)
        n = ctx.draw_int("n_seeds", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 8, 12)
        n = ctx.draw_int("n_seeds", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 6, 9)
        n = ctx.draw_int("n_seeds", 2, 3)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    # Helpful instances keep seeds on distinct down-right diagonals.  Earlier
    # versions sampled cells independently, so normal generation occasionally
    # leaked the declared `two_seeds_same_diag` degenerate: one seed sat on
    # another seed's ray and the overwrite/order branch was hidden.
    positions = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    rng.shuffle(positions)
    max_distinct_diags = len({r - c for r, c in positions})
    n = max(1, min(n, min(9, max_distinct_diags)))
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used_diags: set[int] = set()
    for color in colors:
        placed = False
        for r, c in positions:
            diag = r - c
            if g[r][c] != 0 or diag in used_diags:
                continue
            g[r][c] = color
            used_diags.add(diag)
            placed = True
            break
        if not placed:
            raise ValueError("could not place seeds on distinct down-right diagonals")
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for down-right diagonal seed inputs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    bad = sorted({v for row in grid for v in row if not (0 <= v <= 9)})
    if bad:
        errs.append(f"out-of-range colors: {bad}")
    seeds = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    lo, hi = (1, 2) if difficulty == "easy" else ((3, 5) if difficulty == "hard" else (2, 3))
    if not (lo <= len(seeds) <= hi):
        errs.append(f"expected {lo}..{hi} seed cells for difficulty={difficulty}, got {len(seeds)}")
    colors = [v for _, _, v in seeds]
    if len(colors) != len(set(colors)):
        errs.append(f"seed colors should be distinct, got {colors}")
    edge_seeds = [(r, c) for r, c, _ in seeds if r == h - 1 or c == w - 1]
    if edge_seeds:
        errs.append(f"seed(s) on bottom/right edge have no down-right ray: {edge_seeds}")
    diags = [r - c for r, c, _ in seeds]
    if len(diags) != len(set(diags)):
        errs.append(f"two seeds share a down-right diagonal: {diags}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 5, 6
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid — no diagonals to paint
        return g
    if name == "seed_at_bottom_right":
        # seed at (h-1, w-1) → diagonal length is 1 (just the seed)
        g[h - 1][w - 1] = 5
        return g
    if name == "two_seeds_same_diag":
        # two seeds on the same down-right diagonal → second seed sits inside first ray
        g[1][1] = 4
        g[3][3] = 6
        return g
    return g
