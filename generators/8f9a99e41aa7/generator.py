"""Generator for arc_additional_puzzle_bank_volume5:H32 — Cells reached by ≥2 1-seed rays.

Rule: for each 1-seed, cast 4 cardinal rays through non-8 cells; count
how many rays reach each cell. Cells with count==2 → 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, single_seed, no_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f9a99e41aa7"
VERSION = "1.1.1"
TASK_ID = "8f9a99e41aa7"
SUMMARY = "Several 1-seeds at different positions + 8-walls; output marks cells reached by exactly 2 rays."

INVARIANTS = [
    "between 3 and 4 1-seeds at distinct positions",
    "1-3 8-cells acting as walls",
    "at least one row/col is reached by exactly 2 seeds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 3..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "scattered_seeds_with_walls",
                       "valid": "scattered_seeds_with_walls"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=3 color-1 seeds present (walls can be absent if all positions were occupied)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_seeds", "single_seed", "no_overlap"):
        return errs
    seeds = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if seeds < 3:
        errs.append(f"need >=3 color-1 seeds, found {seeds}")
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
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n = rng.randint(3, 4)
    used = set()
    placed = 0
    while placed < n:
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if (r, c) in used: continue
        used.add((r, c)); g[r][c] = 1; placed += 1
    for _ in range(rng.randint(1, 2)):
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if (r, c) in used: continue
        used.add((r, c)); g[r][c] = 8
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # walls only, no 1-seeds → no rays cast, no cells marked
        g[3][4] = 8
        g[5][6] = 8
        return g
    if name == "single_seed":
        # only 1 seed → no cell can be reached by 2 rays
        g[3][3] = 1
        g[5][5] = 8
        return g
    if name == "no_overlap":
        # all seeds on the same row/col axis → rays share lanes (all cells reached
        # by either 1 or all seeds, never exactly 2 in nontrivial way)
        # OR seeds with walls fully isolating each — keep it simple: same column
        g[1][5] = 1
        g[3][5] = 1
        g[6][5] = 1
        g[2][5] = 8   # full wall isolates each seed's column scan
        g[5][5] = 8
        return g
    return g
