"""Generator for 16b:hard_108 — fill chambers by nearest seed (Manhattan).

Rule: 5-walls form rectangular chambers (2x2). Each chamber holds 1-3
seed cells. Each bg cell within a chamber gets filled with the color
of the nearest (Manhattan) seed; ties broken by lower color value.

Combinatorial axes (8): grid_h, grid_w, palette_kind, ch_h,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_seeds, single_seed_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e26f5e11d316"
VERSION = "1.3.0"  # add executable chamber seed invariant self-check
TASK_ID = "e26f5e11d316"

SUMMARY = "Color-5 walls form rectangular chambers (2×2 grid). Each chamber has 1-3 colored seed cells. Rule fills each bg (0) cell within a chamber with the color of its NEAREST seed (Manhattan); ties broken by lower color value. Walls and seeds stay."

# Rivals: 'output is input' refuted by any demo (chambers fill).
# 'fill with bg color' refuted by any demo (fill uses seed colors).
# 'fill all chambers same color' refuted by ≥2 demos with different
# seeds per chamber. 'pick farthest seed' refuted by any demo (nearest
# wins). 'fill across walls' refuted by any demo where walls block.
# 3 demos with varied chambers cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "5-walls form a 2x2 chamber layout",
    "each chamber has 1-3 isolated seed cells in distinct non-{0,5} colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_seeds", "single_seed_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived", "valid": "11..15"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "11..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "ch_h":           {"type": "int", "default": "rng 4..5", "valid": "3..11"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8..8"},
    "position_bias":  {"type": "str", "default": "5walls_2x2_chambers_with_seeds",
                       "valid": "5walls_2x2_chambers_with_seeds"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_walls|no_seeds|single_seed_only"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        ch = ctx.draw_int("ch_h", 3, 4)
        cw = ctx.draw_int("ch_w", 3, 5)
    elif difficulty == "hard":
        ch = ctx.draw_int("ch_h", 7, 11)
        cw = ctx.draw_int("ch_w", 7, 11)
    else:
        ch = ctx.draw_int("ch_h", 4, 7)
        cw = ctx.draw_int("ch_w", 4, 8)
    rng = ctx.draw_rng("layout")
    h = 2 * ch + 3; w = 2 * cw + 3
    g = full_grid(h, w, 0)
    for c in range(w):
        g[0][c] = 5; g[ch + 1][c] = 5; g[h - 1][c] = 5
    for r in range(h):
        g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
    chambers = [(1, 1), (1, cw + 2), (ch + 2, 1), (ch + 2, cw + 2)]
    for rr, cc in chambers:
        n_seeds = rng.randint(1, 3)
        cells = [(r, c) for r in range(rr, rr + ch) for c in range(cc, cc + cw)]
        slots = rng.sample(cells, n_seeds)
        seed_colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_seeds)
        for (r, c), color in zip(slots, seed_colors):
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    ch, cw = 4, 4
    h = 2 * ch + 3; w = 2 * cw + 3
    if name == "no_walls":
        # seeds without 5-walls → no chambers, undefined Manhattan filling
        g = full_grid(h, w, 0)
        g[2][2] = 4; g[2][8] = 6; g[7][2] = 7; g[7][8] = 8
        return g
    if name == "no_seeds":
        # walls form chambers but no seeds → nothing to fill from
        g = full_grid(h, w, 0)
        for c in range(w):
            g[0][c] = 5; g[ch + 1][c] = 5; g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
        return g
    if name == "single_seed_only":
        # only one chamber has a seed → other chambers undefined
        g = full_grid(h, w, 0)
        for c in range(w):
            g[0][c] = 5; g[ch + 1][c] = 5; g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
        g[2][2] = 4
        return g
    return full_grid(h, w, 0)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errors = []
    wall_rows = [r for r, row in enumerate(grid) if all(v == 5 for v in row)]
    wall_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(wall_rows) != 3 or len(wall_cols) != 3:
        return [f"expected three full wall rows and cols, got {(len(wall_rows), len(wall_cols))}"]
    for ri in range(2):
        for ci in range(2):
            r1, r2 = wall_rows[ri] + 1, wall_rows[ri + 1]
            c1, c2 = wall_cols[ci] + 1, wall_cols[ci + 1]
            colors = [grid[r][c] for r in range(r1, r2) for c in range(c1, c2) if grid[r][c] not in (0, 5)]
            if not (1 <= len(colors) <= 3):
                errors.append("each chamber should contain 1..3 seed cells")
            if len(colors) != len(set(colors)):
                errors.append("seed colors within a chamber should be distinct")
            if any(v in (0, 5) or not (1 <= v <= 9) for v in colors):
                errors.append("seed colors must be non-{0,5} ARC colors")
    return sorted(set(errors))
