"""Generator for arc_puzzle_bank_tenth_21_bundle:easy_66_draw_rectangle_borders_from_corner_pairs.

Each color pair marks opposite corners of a rectangle border.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_endpoint, axis_aligned.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "96aa63433580"
VERSION = "2.0.1"
TASK_ID = "96aa63433580"

SUMMARY = (
    "0-bg grid with N (2-5) distinct colors. Each color appears at "
    "exactly 2 cells positioned as OPPOSITE CORNERS of a rectangle "
    "(so the bbox of those 2 cells defines a rectangle with width and "
    "height both ≥3). Different colors' rectangles may overlap or "
    "nest. Rule: for each color c with ≥2 cells, compute the bbox of "
    "ALL cells of color c, draw the border (outline) of that bbox in "
    "color c on a fresh 0-grid. Colors with <2 cells are ignored. "
    "Output: only the rectangle border outlines appear, no interior fill."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each active color appears at exactly 2 cells",
    "the 2 cells of each color are OPPOSITE corners of a rect with bbox ≥3×3",
    "≥2 active colors so the output has multiple rectangles",
    "rectangles may overlap (not required to be disjoint)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "axis_aligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "4..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "opposite_corner_pairs",
                       "valid": "opposite_corner_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 active colors each appearing exactly twice at opposite corners of a ≥3×3 bbox."""
    if not grid or not grid[0]:
        return ["empty grid"]
    from collections import defaultdict
    pos: dict = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                pos[v].append((r, c))
    errs = []
    rect_pairs = 0
    for v, cells in pos.items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        if r0 != r1 and c0 != c1 and abs(r1 - r0) >= 2 and abs(c1 - c0) >= 2:
            rect_pairs += 1
    if rect_pairs < 1:
        errs.append(f"expected >=1 color with 2 cells at opposite corners of >=3x3 bbox; found {rect_pairs}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        target = ctx.draw_int("rectangles", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 14, 18)
        target = ctx.draw_int("rectangles", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 15)
        target = ctx.draw_int("rectangles", 3, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(colors)
    used: set[tuple[int, int]] = set()
    placed = 0
    for color in colors:
        if placed >= target:
            break
        for _ in range(120):
            r0, r1 = sorted(rng.sample(range(h), 2))
            c0, c1 = sorted(rng.sample(range(w), 2))
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue
            corners = [(r0, c0), (r1, c1)]
            if any(p in used for p in corners):
                continue
            for r, c in corners:
                g[r][c] = color
            used.update(corners)
            placed += 1
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no opposite-corner pairs to define rectangles
        return g
    if name == "single_endpoint":
        # 1 cell per color → can't form pair, no rectangle defined
        g[2][2] = 4; g[5][7] = 6
        return g
    if name == "axis_aligned":
        # 2 cells in same row → degenerate to a line, no rectangle
        g[3][1] = 4; g[3][8] = 4
        return g
    return g
