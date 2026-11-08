"""Generator for 17b:hard_116 — fill chambers by priority seed.

Rule: top row holds priority legend. 5-walls form chambers below.
Each chamber filled with the highest-priority seed color present.

Combinatorial axes (8): ch_h, ch_w, palette_kind, n_legend, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_seeds, no_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "adfbfbdb73c3"
VERSION = "2.0.1"
TASK_ID = "adfbfbdb73c3"

SUMMARY = (
    "0-bg grid with: (a) ROW 0 holding a LEGEND "
    "of 3 distinct non-{0, 5} PRIORITY COLORS at "
    "columns 1, 2, 3 (left-to-right priority "
    "order, leftmost = highest priority); (b) "
    "ROWS 2..h-1 forming a 5-WALLED REGION — "
    "color-5 (gray) outer FRAME (row 2 = top "
    "wall, row h-1 = bottom wall, cols 0 and "
    "w-1 = side walls) plus an INTERNAL VERTICAL "
    "WALL at col cw+1 that splits the region "
    "into 2 CHAMBERS; (c) each chamber holds "
    "1-2 SEED CELLS (single pixels) using colors "
    "from the legend. Rule: for EACH CHAMBER "
    "independently, find all seeds and "
    "determine the SEED COLOR WITH HIGHEST "
    "PRIORITY (leftmost legend position). FILL "
    "every empty (bg) cell inside that chamber "
    "(not the walls, not the seeds) with that "
    "highest-priority color. Net: each chamber "
    "flood-fills to its dominant seed-priority "
    "color; walls and legend stay."
)

INVARIANTS = [
    "background is 0",
    "row 0 holds 3 distinct non-{0,5} priority colors at distinct columns",
    "5-walls form 2 chambers below row 1 (outer 5-frame + 1 internal vertical wall)",
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
    "n_legend":       {"type": "int", "default": "3", "valid": "3..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "legend_top_chambers_below",
                       "valid": "legend_top_chambers_below"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, color-5 walls present, row-0 has non-{0,5} legend cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_legend", "no_walls"):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_5 = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    legend_colors = [grid[0][c] for c in range(w) if grid[0][c] not in (0, 5)]
    if not has_5:
        errs.append("no color-5 wall cells found")
    if len(legend_colors) < 1:
        errs.append("row-0 has no legend (non-{0,5}) cells")
    return errs


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
    h = ch + 4
    w = 2 * cw + 3
    g = full_grid(h, w, 0)
    legend = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    for j, v in enumerate(legend): g[0][j + 1] = v
    walls_c = [0, cw + 1, w - 1]
    for c in range(w):
        g[2][c] = 5; g[h - 1][c] = 5
    for r in range(2, h):
        for wc in walls_c: g[r][wc] = 5
    chamber_cols = [(walls_c[i] + 1, walls_c[i + 1] - 1) for i in range(2)]
    for c_lo, c_hi in chamber_cols:
        n_seeds = rng.randint(1, 2)
        cells = [(r, c) for r in range(3, h - 1) for c in range(c_lo, c_hi + 1)]
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
    walls_c = [0, cw + 1, w - 1]
    if name == "no_legend":
        # Walls and seeds present but row 0 is empty — rule has no priority
        # ranking to select chamber fill colors from.
        for c in range(w):
            g[2][c] = 5; g[h - 1][c] = 5
        for r in range(2, h):
            for wc in walls_c: g[r][wc] = 5
        g[4][2] = 4; g[5][6] = 6
        return g
    if name == "no_seeds":
        # Legend + walls but chambers are empty — no seed determines a fill color.
        for j, v in enumerate([1, 2, 3]): g[0][j + 1] = v
        for c in range(w):
            g[2][c] = 5; g[h - 1][c] = 5
        for r in range(2, h):
            for wc in walls_c: g[r][wc] = 5
        return g
    if name == "no_walls":
        # Legend + seeds but no 5-walls — chamber boundaries undefined.
        for j, v in enumerate([1, 2, 3]): g[0][j + 1] = v
        g[4][2] = 1; g[5][6] = 2
        return g
    return g
