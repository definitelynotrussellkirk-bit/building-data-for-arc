"""Generator for 18b:hard_123 — fill chambers by seed priority legend.

Rule: top row legend (cols 0-2) ranks 3 colors. 5-walls form 2x2
chambers. Each chamber has 1-2 seed cells with colors from the legend.
Output fills each chamber's bg cells with the highest-priority seed
color (earliest in legend); seeds keep their colors.

Combinatorial axes (8): ch_h, ch_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_seeds, no_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a5b0638997f5"
VERSION = "1.2.0"
TASK_ID = "a5b0638997f5"
SUMMARY = "Top legend (3-color priority) + 2x2 5-walled chambers with 1-2 seeds each."

INVARIANTS = [
    "background is 0",
    "top row cols 0..2 hold the 3-color legend (priority order)",
    "5-walls form a 2x2 chamber layout below the legend row",
    "each chamber has 1-2 seed cells using legend colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_seeds", "no_walls")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "ch_h":           {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "ch_w":           {"type": "int", "default": "3", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "legend_top_chambers_below",
                       "valid": "legend_top_chambers_below"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        ch = ctx.draw_int("ch_h", 2, 2)
        cw = ctx.draw_int("ch_w", 3, 3)
    elif difficulty == "hard":
        ch = ctx.draw_int("ch_h", 3, 4)
        cw = ctx.draw_int("ch_w", 3, 4)
    else:
        ch = ctx.draw_int("ch_h", 2, 3)
        cw = ctx.draw_int("ch_w", 3, 3)
    rng = ctx.draw_rng("layout")
    h = 2 * ch + 4
    w = 2 * cw + 3
    g = full_grid(h, w, 0)
    legend = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    for j, v in enumerate(legend): g[0][j] = v
    for c in range(w):
        g[1][c] = 5; g[ch + 2][c] = 5; g[h - 1][c] = 5
    for r in range(1, h):
        g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
    chambers = [(2, 1), (2, cw + 2), (ch + 3, 1), (ch + 3, cw + 2)]
    for rr, cc in chambers:
        n_seeds = rng.randint(1, 2)
        cells = [(r, c) for r in range(rr, rr + ch) for c in range(cc, cc + cw)]
        slots = rng.sample(cells, n_seeds)
        seed_colors = rng.sample(legend, n_seeds)
        for (r, c), color in zip(slots, seed_colors): g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    ch, cw = 2, 3
    h = 2 * ch + 4
    w = 2 * cw + 3
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # Walls + seeds present but row-0 legend is missing — rule's
        # priority-ranking step has no order to read.
        for c in range(w):
            g[1][c] = 5; g[ch + 2][c] = 5; g[h - 1][c] = 5
        for r in range(1, h):
            g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
        g[2][1] = 3; g[ch + 3][cw + 2] = 7
        return g
    if name == "no_seeds":
        # Legend + walls present but chambers are empty — rule has no
        # seed colors to choose between.
        g[0][0] = 3; g[0][1] = 7; g[0][2] = 2
        for c in range(w):
            g[1][c] = 5; g[ch + 2][c] = 5; g[h - 1][c] = 5
        for r in range(1, h):
            g[r][0] = 5; g[r][cw + 1] = 5; g[r][w - 1] = 5
        return g
    if name == "no_walls":
        # Legend + seeds but no 5-walls — chamber boundaries are
        # undefined, rule has no regions to fill.
        g[0][0] = 3; g[0][1] = 7; g[0][2] = 2
        g[3][2] = 3; g[5][6] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0])
    if (h - 4) % 2 != 0 or (w - 3) % 2 != 0:
        return ["grid dimensions must match the 2x2 chamber construction"]
    ch = (h - 4) // 2
    cw = (w - 3) // 2
    legend = grid[0][:3]
    if len(set(legend)) != 3 or any(v in {0, 5} for v in legend):
        msgs.append("top legend must contain three distinct nonzero non-wall colors")
    wall_rows = {1, ch + 2, h - 1}
    wall_cols = {0, cw + 1, w - 1}
    for r in range(1, h):
        for c in range(w):
            if r in wall_rows or c in wall_cols:
                if grid[r][c] != 5:
                    msgs.append("5-walls must form a complete 2x2 chamber lattice")
                    break
        else:
            continue
        break
    chambers = [(2, 1), (2, cw + 2), (ch + 3, 1), (ch + 3, cw + 2)]
    for rr, cc in chambers:
        seeds = [(r, c) for r in range(rr, rr + ch) for c in range(cc, cc + cw) if grid[r][c] != 0]
        if not (1 <= len(seeds) <= 2):
            msgs.append("each chamber must contain one or two seed cells")
        if any(grid[r][c] not in legend for r, c in seeds):
            msgs.append("chamber seeds must use legend colors")
    return msgs
