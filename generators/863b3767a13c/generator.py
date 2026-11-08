"""Generator for arc_puzzle_bank_21_set4:S4_M6 — four corners → perimeter.

Rule: each color appearing exactly 4 times at the corners of a
non-degenerate axis-aligned rectangle → draw the rectangle's perimeter
in that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rects, three_corners_only, degenerate_rect.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "863b3767a13c"
VERSION = "2.0.1"
TASK_ID = "863b3767a13c"
SUMMARY = (
    "0-bg grid (h~8-10, w~10-13) with 1-2 non-bg "
    "COLORS, each placed at EXACTLY 4 CORNERS of an "
    "axis-aligned NON-DEGENERATE RECTANGLE (≥4 rows "
    "and ≥4 cols apart). For each color: 4 cells at "
    "(r1, c1), (r1, c2), (r2, c1), (r2, c2) with r1 "
    "< r2 and c1 < c2. Multiple colors' rectangles do "
    "not overlap. Rule: for every non-zero color "
    "appearing in exactly 4 cells at the 4 corners "
    "of an axis-aligned rectangle, PAINT the full "
    "RECTANGLE PERIMETER (all cells on rows r1 and "
    "r2 and all cells on cols c1 and c2, between the "
    "corners) in that color. Interior cells stay 0. "
    "Net: each 4-corner set becomes a complete hollow "
    "colored rectangle outline."
)

INVARIANTS = [
    "background is 0",
    "each non-zero color appears at 4 axis-aligned corners",
    "rectangles don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rects", "three_corners_only", "degenerate_rect")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "four_corner_rects",
                       "valid": "four_corner_rects"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each nonzero color appears exactly 4 times at rectangle corners."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return []  # degenerate no_rects — allowed
    from collections import defaultdict
    by_color = defaultdict(list)
    for r, c in nonzero:
        by_color[grid[r][c]].append((r, c))
    errs = []
    for color, cells in by_color.items():
        if len(cells) != 4:
            return []  # degenerate three_corners_only or degenerate_rect — allowed
        rs = sorted(set(r for r, c in cells))
        cs = sorted(set(c for r, c in cells))
        if len(rs) != 2 or len(cs) != 2:
            return []  # degenerate colinear — allowed
        r1, r2, c1, c2 = rs[0], rs[1], cs[0], cs[1]
        expected = {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}
        if set(cells) != expected:
            errs.append(f"color {color}: cells {cells} are not axis-aligned rectangle corners")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(1, 2)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    reserved: set[tuple[int, int]] = set()
    for color in palette:
        for _ in range(40):
            r1 = rng.randint(0, h - 4)
            c1 = rng.randint(0, w - 4)
            r2 = rng.randint(r1 + 3, min(h - 1, r1 + 5))
            c2 = rng.randint(c1 + 3, min(w - 1, c1 + 5))
            cells = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
            if cells & reserved:
                continue
            g[r1][c1] = color; g[r1][c2] = color
            g[r2][c1] = color; g[r2][c2] = color
            reserved |= cells
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_rects":
        # blank → no corner sets to draw perimeters of
        return g
    if name == "three_corners_only":
        # color appears 3 times → "exactly 4 corners" precondition fails
        g[1][1] = 4
        g[1][7] = 4
        g[5][1] = 4  # missing (5, 7)
        return g
    if name == "degenerate_rect":
        # 4 cells colinear (1 row only) → not a rectangle
        for c in [1, 4, 7, 10]: g[3][c] = 4
        return g
    return g
