"""Generator for arc_puzzle_bank_fourteenth21:E98.

Place matching opposite-corner pairs whose bounding rectangles get filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_endpoint, axis_aligned.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a8926bd9d9f"
VERSION = "2.0.1"
TASK_ID = "7a8926bd9d9f"

SUMMARY = (
    "0-bg grid (h~8-10, w~"
    "8-10) with 2-3 PAIRS "
    "of OPPOSITE-CORNER "
    "CELLS in DISTINCT "
    "colors from {1..9}. "
    "Each PAIR has two "
    "cells placed at "
    "DIAGONALLY OPPOSITE "
    "CORNERS of an axis-"
    "aligned rectangle of "
    "size 2-4 × 2-5 (TL/BR "
    "OR TR/BL, randomly "
    "chosen). The rectangles "
    "between pairs are "
    "DISJOINT (no cell "
    "shared). Rule (FILL "
    "EACH OPPOSITE-CORNER "
    "PAIR'S BOUNDING "
    "RECTANGLE WITH ITS "
    "COLOR): For EACH "
    "COLOR appearing as "
    "EXACTLY 2 CELLS at "
    "(r1, c1) and (r2, "
    "c2) — diagonal corners "
    "of an axis-aligned "
    "rectangle: PAINT "
    "every cell at rows "
    "min(r1, r2)..max(r1, "
    "r2), cols min(c1, "
    "c2)..max(c1, c2) "
    "(inclusive — the "
    "full filled rectangle)"
    " with that color. "
    "Net: each pair of "
    "diagonal corners "
    "fills in to a solid "
    "rectangle of its "
    "color."
)

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "same-color cells are opposite rectangle corners",
    "filled rectangle regions are disjoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "axis_aligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "opposite_corner_pairs",
                       "valid": "opposite_corner_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, each non-zero color appears exactly twice."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        errs.append("no nonzero cells found")
        return errs
    bad = [c for c, n in counts.items() if n != 2]
    if bad:
        errs.append(f"color(s) {bad} don't appear exactly twice; each color needs 2 corner cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("rectangles", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("rectangles", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        target = ctx.draw_int("rectangles", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=target)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        rh = rng.randint(2, min(4, h))
        rw = rng.randint(2, min(5, w))
        r1 = rng.randint(0, h - rh)
        c1 = rng.randint(0, w - rw)
        r2 = r1 + rh - 1
        c2 = c1 + rw - 1
        rect = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        if rect & reserved:
            continue
        color = colors[placed]
        if rng.randrange(2):
            a, b = (r1, c1), (r2, c2)
        else:
            a, b = (r1, c2), (r2, c1)
        g[a[0]][a[1]] = color
        g[b[0]][b[1]] = color
        reserved.update(rect)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no opposite-corner pairs to define rectangles
        return g
    if name == "single_endpoint":
        # 1 cell per color → can't form pair
        g[2][2] = 4
        g[5][6] = 6
        return g
    if name == "axis_aligned":
        # 2 cells in same row → degenerate to a line, no rectangle
        g[3][1] = 4; g[3][7] = 4
        return g
    return g
