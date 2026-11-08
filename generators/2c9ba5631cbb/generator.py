"""Generator for 18b:hard_125 — fill chambers by nearest seed.

Rule: 5-walls form 2x2 rectangular chambers. Each chamber has one
non-bg, non-5 seed cell. Output fills each chamber with its seed
color (replacing all bg cells in the chamber).

Combinatorial axes (8): grid_h, grid_w, palette_kind, ch_h,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_seeds, multiple_seeds_per_chamber.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c9ba5631cbb"
VERSION = "2.0.1"  # in=4 (few grid sizes): widened chamber dims ch/cw {3,4}->2..6 incl. non-square -> more grid shapes. 2x2-chamber flood-fill rule unchanged.
TASK_ID = "2c9ba5631cbb"
SUMMARY = "5-grid (2x2 chambers) with 1 distinct-color seed per chamber."

INVARIANTS = [
    "background is 0",
    "5-walls form a 2x2 chamber layout (outer frame + 1 horizontal + 1 vertical divider)",
    "each chamber has exactly one non-bg, non-5 seed cell, all 4 colors distinct",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_seeds", "multiple_seeds_per_chamber")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived", "valid": "9..15"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "9..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "ch_h":           {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "ch_w":           {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "five_walls_2x2_chambers_with_seeds",
                       "valid": "five_walls_2x2_chambers_with_seeds"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-5 wall cells, exactly 4 distinct non-{0,5} seed cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w))
    errs = []
    if counts.get(5, 0) == 0:
        errs.append("no color-5 (wall) cells found")
    seeds = {c: n for c, n in counts.items() if c not in (0, 5)}
    if len(seeds) != 4:
        errs.append(f"expected exactly 4 distinct seed colors, got {len(seeds)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # chamber dims drive grid size (h=2ch+3); rule floods any chamber size, so widen
    # ch/cw (was {3,4} -> only 4 grid sizes / in=4) incl. non-square chambers.
    if difficulty == "easy":
        ch = ctx.draw_int("ch_h", 2, 3)
        cw = ctx.draw_int("ch_w", 2, 3)
    elif difficulty == "hard":
        ch = ctx.draw_int("ch_h", 4, 6)
        cw = ctx.draw_int("ch_w", 4, 6)
    else:
        ch = ctx.draw_int("ch_h", 2, 5)
        cw = ctx.draw_int("ch_w", 2, 5)
    rng = ctx.draw_rng("layout")
    h = 2 * ch + 3
    w = 2 * cw + 3
    g = full_grid(h, w, 0)
    for c in range(w):
        g[0][c] = 5; g[ch + 1][c] = 5; g[h - 1][c] = 5
    for r in range(h):
        g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 4)
    chambers = [(1, 1), (1, cw + 2), (ch + 2, 1), (ch + 2, cw + 2)]
    for color, (rr, cc) in zip(palette, chambers):
        sr = rng.randint(rr, rr + ch - 1)
        sc = rng.randint(cc, cc + cw - 1)
        g[sr][sc] = color
    return g


def _draw_from_degenerate(name, rng):
    ch, cw = 3, 3
    h = 2 * ch + 3
    w = 2 * cw + 3
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # seeds without walls → no chambers, can't fill within boundaries
        g[1][1] = 4; g[2][6] = 6
        g[5][2] = 7; g[6][7] = 8
        return g
    if name == "no_seeds":
        # walls form chambers but no seeds → nothing to flood
        for c in range(w):
            g[0][c] = 5; g[ch + 1][c] = 5; g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
        return g
    if name == "multiple_seeds_per_chamber":
        # one chamber has 2 seeds → "exactly one seed" precondition fails
        for c in range(w):
            g[0][c] = 5; g[ch + 1][c] = 5; g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
        g[1][1] = 4; g[2][2] = 6  # both in TL chamber
        g[1][5] = 7
        g[5][1] = 8
        return g
    return g
