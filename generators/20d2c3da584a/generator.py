"""Generator for arc_puzzle_bank_twelfth_21_bundle:easy_82_draw_object_bounding_boxes.

Rule: each monochrome object keeps its cells and gains its bounding-box border.

Combinatorial axes (8): grid_h, grid_w, palette_kind, objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, single_cell_objects, solid_rect_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "20d2c3da584a"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one non-zero cell (monochrome component(s) to draw bboxes)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        errs.append("no non-zero cells (expected monochrome components to draw bboxes)")
    return errs
TASK_ID = "20d2c3da584a"

SUMMARY = (
    "0-bg grid (h~8-12, w~"
    "9-14) with 2-4 "
    "MONOCHROME CONNECTED "
    "COMPONENTS — each a "
    "4-cell L-shape (or "
    "similar) chosen from "
    "a small shape bank, "
    "in a DISTINCT COLOR "
    "from {1..9} drawn per "
    "component. "
    "Components are placed "
    "at non-touching "
    "positions with 1-cell "
    "padding (8-conn "
    "buffer check). Each "
    "component has a non-"
    "trivial bbox (h × w "
    "= 3 × 2 / 3 × 3 / "
    "2 × 3). Rule (PAINT "
    "EACH COMPONENT'S "
    "BBOX BORDER, KEEP "
    "ORIGINAL CELLS): For "
    "EACH MONOCHROME "
    "CONNECTED COMPONENT "
    "of color C with bbox "
    "(r1, c1, r2, c2): "
    "PAINT every cell on "
    "the BBOX OUTLINE "
    "(top row r1, bottom "
    "row r2, left col c1, "
    "right col c2 of the "
    "bbox) with color C. "
    "INTERIOR bg cells "
    "(strictly inside the "
    "bbox) STAY 0. The "
    "original component "
    "cells stay (they "
    "merge with the "
    "border paint). Net: "
    "each L-blob gains a "
    "rectangular outline "
    "around itself in its "
    "own color."
)

# Rivals: 'output is input' refuted by any demo with non-rect blobs.
# 'fill entire bbox' refuted by any demo where interior bg cells stay.
# 'use bg color for border' refuted by any demo (border = blob color).
# 'separate component bboxes overwrite each other' refuted by demos
# with isolated components keeping their own borders. 3 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each component is monochrome and connected",
    "components have nontrivial bounding boxes",
    "component bounding boxes are separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "single_cell_objects", "solid_rect_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "objects":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_l_shapes",
                       "valid": "spaced_l_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_objects|single_cell_objects|solid_rect_objects'},
}


def _free(g, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        target = ctx.draw_int("objects", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 16, 20)
        target = ctx.draw_int("objects", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        target = ctx.draw_int("objects", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shapes = [
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ]
    placed = 0
    for _ in range(160):
        if placed >= target:
            break
        shape = rng.choice(shapes)
        r0 = rng.randint(0, h - 3)
        c0 = rng.randint(0, w - 3)
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        if _free(g, cells):
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            for r, c in cells:
                g[r][c] = color
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # blank → no objects, rule has no bboxes to draw
        return g
    if name == "single_cell_objects":
        # 1x1 objects → bbox = single cell, rule is identity
        g[1][2] = 4
        g[5][7] = 6
        g[7][3] = 3
        return g
    if name == "solid_rect_objects":
        # solid 3x3 rectangles → bbox border = object border, rule is identity
        for r in range(3):
            for c in range(3): g[1 + r][1 + c] = 4
        for r in range(3):
            for c in range(3): g[5 + r][6 + c] = 6
        return g
    return g
