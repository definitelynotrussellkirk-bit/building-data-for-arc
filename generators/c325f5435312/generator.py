"""Generator for arc_puzzle_bank_twelfth_21_bundle:easy_79_fill_rectangles_from_diagonal_corners.

Rule: same-color opposite rectangle corners define a filled rectangle.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, rectangles, texture.
Degenerates: no_pairs, single_corner, collinear_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c325f5435312"
VERSION = "2.0.1"
TASK_ID = "c325f5435312"

SUMMARY = (
    "0-bg grid (h~9-13, w~9-14) with 2-3 "
    "RECTANGLE-CORNER PAIRS — for each "
    "rect: 2 same-color cells placed at "
    "DIAGONALLY OPPOSITE CORNERS of an "
    "implied axis-aligned rectangle "
    "(either main-diagonal (r0,c0)+(r1,c1) "
    "or anti-diagonal (r0,c1)+(r1,c0)). "
    "Each pair uses a DISTINCT color "
    "(2-3 colors total). Implied rects are "
    "3..5 rows × 3..6 cols, with 1-cell "
    "buffer between rects (no overlap). "
    "Rule: for EACH PAIR of SAME-COLOR "
    "CELLS, INTERPRET them as DIAGONALLY "
    "OPPOSITE CORNERS of an axis-aligned "
    "rectangle. FILL the entire rectangle "
    "interior (all cells in "
    "(min_r..max_r) × (min_c..max_c)) "
    "with the pair's COLOR. Net: each "
    "diagonal corner pair becomes a "
    "filled rectangle in its color."
)

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "matching cells are opposite corners of an axis-aligned rectangle",
    "implied rectangles do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_corner", "collinear_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rectangles":     {"type": "int", "default": "rng 2..3", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "= rectangles", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_diagonal_corners",
                       "valid": "scattered_diagonal_corners"},
    "n_distinct_colors": {"type": "int", "default": "= rectangles", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free_rect(g, r0, c0, r1, c1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r1 >= h or c1 >= w:
        return False
    for r in range(max(0, r0 - 1), min(h, r1 + 2)):
        for c in range(max(0, c0 - 1), min(w, c1 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("rectangles", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        target = ctx.draw_int("rectangles", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 9, 14)
        target = ctx.draw_int("rectangles", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, target))
    placed = 0
    for _ in range(180):
        if placed >= target:
            break
        rh = rng.randint(3, min(5, h))
        rw = rng.randint(3, min(6, w))
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        r1, c1 = r0 + rh - 1, c0 + rw - 1
        if not _free_rect(g, r0, c0, r1, c1):
            continue
        color = colors[placed % len(colors)]
        if rng.choice([False, True]):
            corners = [(r0, c0), (r1, c1)]
        else:
            corners = [(r0, c1), (r1, c0)]
        for r, c in corners:
            g[r][c] = color
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Each nonzero color appears exactly twice; pairs span distinct rows and cols (diagonal corners)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    from collections import defaultdict
    pos: dict = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                pos[grid[r][c]].append((r, c))
    for color, cells in pos.items():
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times (expected 2)")
            continue
        (r0, c0), (r1, c1) = cells
        if r0 == r1 or c0 == c1:
            errors.append(f"color {color} endpoints are collinear (same row or col)")
    if not pos:
        errors.append("no nonzero cells found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no diagonal pairs to fill.
        return g
    if name == "single_corner":
        # Color appears once — rule's "exactly twice" filter excludes;
        # rectangle undefined.
        g[3][3] = 4
        return g
    if name == "collinear_corners":
        # Same color on the same row or column — implied rectangle is
        # 1-D, rule's filled-rectangle collapses to a line.
        g[3][2] = 4; g[3][7] = 4
        return g
    return g
