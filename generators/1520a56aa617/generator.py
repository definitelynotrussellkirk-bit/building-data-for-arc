"""Generator for 19b:hard_130 — fill chambers by legend priority.

Rule: top row holds a priority legend of colors (excluding 0 and 8).
Body has 8-walls forming chambers; each chamber may contain seed cells
in legend colors. For each chamber, find seeds present and fill with
the highest-priority (earliest in legend) seed color.

Combinatorial axes (8): ch_h, ch_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_seeds, no_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1520a56aa617"
# 2.1.0: reverse-diversity / canonical-match -- previous version built ONLY two
# vertical chambers; canonical demos use a GRID of chambers (3 cols, or 2x2 with
# an internal horizontal wall). Now build R x C chamber grids (1-2 rows x 2-3
# cols) with legends sized to colors needed. Rule handles arbitrary 8-walled
# regions via BFS; more chamber layouts -> more output shapes/diversity.
VERSION = "2.1.0"
TASK_ID = "1520a56aa617"

SUMMARY = (
    "0-bg grid (h = ch + 4, w = 2*cw "
    "+ 3 with ch=4-5, cw=4-5) "
    "structured as: (a) ROW 0 = "
    "PRIORITY LEGEND with 3 DISTINCT "
    "COLORS (from {1, 2, 3, 4, 5, 6, "
    "7, 9}, exclude 8) at cols 1, 2, "
    "3 (sorted left = highest "
    "priority); (b) FULL-WIDTH "
    "COLOR-8 HORIZONTAL WALL at "
    "ROW 2; (c) FULL-HEIGHT COLOR-8 "
    "VERTICAL WALLS at cols 0, "
    "cw+1, w-1 (outer + 1 internal "
    "divider) starting from row 2; "
    "(d) FULL-WIDTH COLOR-8 "
    "HORIZONTAL WALL at ROW h-1. "
    "This creates an R x C chamber grid "
    "(1-2 rows by 2-3 cols). (e) Inside each chamber: "
    "1-2 SEED CELLS in legend "
    "colors. Rule (CHAMBER FILL BY "
    "LEGEND PRIORITY): for EACH "
    "CHAMBER, identify the SEEDS "
    "present and find the one with "
    "the HIGHEST PRIORITY (= "
    "EARLIEST in the row-0 legend). "
    "FILL the entire chamber's 0-"
    "cells with that priority color. "
    "Walls + legend stay. Net: each "
    "chamber gets flooded with its "
    "highest-priority seed color."
)

INVARIANTS = [
    "background is 0",
    "row 0 holds a 3-5 color priority legend at distinct columns (no 0 or 8)",
    "8-walls form an R x C grid of chambers in rows 2+ (R=1-2 rows, C=2-3 cols)",
    "each chamber holds 1-2 seed cells using legend colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_seeds", "no_walls")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "ch_h":           {"type": "int", "default": "rng 4..5", "valid": "3..7"},
    "ch_w":           {"type": "int", "default": "rng 4..5", "valid": "3..6"},
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
        ch = ctx.draw_int("ch_h", 4, 4)
        cw = ctx.draw_int("ch_w", 4, 4)
    elif difficulty == "hard":
        ch = ctx.draw_int("ch_h", 5, 6)
        cw = ctx.draw_int("ch_w", 5, 6)
    else:
        ch = ctx.draw_int("ch_h", 4, 5)
        cw = ctx.draw_int("ch_w", 4, 5)
    rng = ctx.draw_rng("layout")
    # Chamber grid: n_cols vertical chambers x n_rows horizontal chambers.
    n_cols = rng.randint(2, 3)
    n_rows = rng.randint(1, 2)
    legend = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], rng.randint(3, 5))

    # Layout columns: outer wall, cw, wall, cw, ... ; rows similarly below the
    # legend row (row 0) and the top double-wall (rows 1,2).
    # Total width = 1 (left wall) + n_cols*cw + n_cols (interior+right walls).
    w = 1 + n_cols * cw + n_cols
    # Body chambers start after rows 0 (legend), 1 (blank/wall buffer), 2 (wall).
    # Each chamber row: ch interior + 1 wall below; plus the wall at row 2 above.
    h = 3 + n_rows * (ch + 1)
    g = full_grid(h, w, 0)

    # Legend on row 0.
    for j, v in enumerate(legend):
        g[0][j + 1] = v

    # Top double wall at rows 1 and 2 (full width).
    for c in range(w):
        g[1][c] = 8
        g[2][c] = 8

    # Vertical wall columns.
    walls_c = [0]
    for i in range(n_cols):
        walls_c.append(walls_c[-1] + cw + 1)
    # Horizontal wall rows (below each chamber band), including row 2 (top) and
    # the bottom border.
    walls_r = [2]
    for i in range(n_rows):
        walls_r.append(walls_r[-1] + ch + 1)

    for r in range(2, h):
        for wc in walls_c:
            g[r][wc] = 8
    for wr in walls_r:
        for c in range(w):
            g[wr][c] = 8

    # Each chamber is the interior between consecutive wall rows/cols.
    for ri in range(n_rows):
        r_lo = walls_r[ri] + 1
        r_hi = walls_r[ri + 1] - 1
        for ci in range(n_cols):
            c_lo = walls_c[ci] + 1
            c_hi = walls_c[ci + 1] - 1
            cells = [(r, c) for r in range(r_lo, r_hi + 1)
                     for c in range(c_lo, c_hi + 1)]
            if not cells:
                continue
            n_seeds = rng.randint(1, min(2, len(legend), len(cells)))
            slots = rng.sample(cells, n_seeds)
            seed_colors = rng.sample(legend, n_seeds)
            for (r, c), color in zip(slots, seed_colors):
                g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    ch, cw = 4, 4
    h = ch + 4
    w = 2 * cw + 3
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # Walls + seeds present but row 0 has no legend — rule has
        # no priority order to consult.
        for c in range(w):
            g[2][c] = 8; g[h - 1][c] = 8
        for r in range(2, h):
            for wc in [0, cw + 1, w - 1]: g[r][wc] = 8
        g[3][2] = 3; g[5][cw + 3] = 7
        return g
    if name == "no_seeds":
        # Legend + walls present but chambers are empty — rule has no
        # seeds to rank.
        for j, v in enumerate([3, 7, 2]): g[0][j + 1] = v
        for c in range(w):
            g[2][c] = 8; g[h - 1][c] = 8
        for r in range(2, h):
            for wc in [0, cw + 1, w - 1]: g[r][wc] = 8
        return g
    if name == "no_walls":
        # Legend + seeds but body has no 8-walls — chamber regions are
        # undefined, rule has nothing to fill.
        for j, v in enumerate([3, 7, 2]): g[0][j + 1] = v
        g[3][2] = 3; g[5][cw + 3] = 7
        return g
    return g



def _regions_without_wall(grid, wall=8):
    h, w = len(grid), len(grid[0])
    seen = set(); regs = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == wall or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != wall and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            regs.append(cells)
    return regs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    legend = [v for v in grid[0] if v not in (0, 8)]
    if not (3 <= len(legend) <= 5) or len(set(legend)) != len(legend):
        errs.append(f"row 0 must hold 3..5 distinct legend colors excluding 0/8, got {legend}")
    if any(v == 8 for v in grid[0]):
        errs.append("legend row should not contain wall color 8")
    if h < 5 or w < 7:
        errs.append("grid too small for chamber layout")
    body = [row[:] for row in grid[2:]]
    regs = _regions_without_wall(body, 8)
    rooms = [reg for reg in regs if reg]
    if not (2 <= len(rooms) <= 6):
        errs.append(f"expected 2..6 chambers in body, found {len(rooms)}")
    for reg in rooms:
        vals = [body[r][c] for r, c in reg]
        seeds = [v for v in vals if v in legend]
        if not (1 <= len(seeds) <= 2):
            errs.append("each chamber must have 1-2 legend-colored seeds")
        if any(v not in (0, *legend) for v in vals):
            errs.append("chamber contains a nonzero non-legend seed color")
    return errs
