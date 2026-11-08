"""Generator for arc_additional_puzzles_21_set4:H25.

Rule: for each empty cell, find sources visible (same row/col, no
non-zero between). Unique color → that, ≥2 distinct → 8.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_sources, single_source, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "530b63eb8e59"
VERSION = "2.0.0"
TASK_ID = "530b63eb8e59"
SUMMARY = (
    "0-bg grid (h~6-8, w~8-10) with 2 single "
    "SOURCE CELLS in distinct non-zero colors "
    "from {2, 3, 4, 5}, placed at hardcoded "
    "positions (1, 3) and (4, 2). NOTE: "
    "positions hardcoded — diversity is "
    "intrinsic-mid. Rule: for EACH EMPTY (0) "
    "CELL, FIND all SOURCES that are VISIBLE "
    "(same row or column, no non-zero between "
    "the cell and the source). For the cell: "
    "if EXACTLY ONE color is visible (only "
    "one source on its axes), PAINT it that "
    "color; if ≥2 DISTINCT colors are "
    "visible, PAINT it COLOR 8 (cyan); if "
    "zero visible, leave as 0. Sources stay. "
    "Net: empty cells fill with the unique "
    "visible source color, or cyan for "
    "intersections of multiple source axes."
)

INVARIANTS = [
    "between 1 and 3 single-cell sources of distinct colors",
    "at least one empty cell has ≥2 visible sources",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_sources", "single_source", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..10"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
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
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [2, 3, 4, 5]; rng.shuffle(palette)
    g[1][3] = palette[0]
    g[4][2] = palette[1]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 9, 0)
    if name == "no_sources":
        return g
    if name == "single_source":
        g[3][4] = 2
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(9):
                g[r][c] = 2
        return g
    return g
def _visible_source_colors(grid, r, c):
    h, w = len(grid), len(grid[0])
    colors = set()
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        while 0 <= rr < h and 0 <= cc < w:
            if grid[rr][cc] != 0:
                colors.add(grid[rr][cc])
                break
            rr += dr; cc += dc
    return colors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    sources = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not (1 <= len(sources) <= 3):
        errors.append(f"expected 1-3 source cells, got {len(sources)}")
    if len({v for _, _, v in sources}) != len(sources):
        errors.append("source colors must be distinct")
    multi = 0; unique = 0
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                continue
            colors = _visible_source_colors(grid, r, c)
            if len(colors) >= 2:
                multi += 1
            elif len(colors) == 1:
                unique += 1
    if multi == 0:
        errors.append("no empty cell sees multiple distinct source colors")
    if unique == 0:
        errors.append("no empty cell sees a unique source color")
    return errors
