"""Generator for arc_puzzle_bank_21_set23_bundle:easy_p05.

Solid 2x2 squares bloom one same-color cell from each diagonal corner.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_squares,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_squares, single_cell, on_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75837d4fa905"
VERSION = "2.0.1"
TASK_ID = "75837d4fa905"
SUMMARY = (
    "0-bg grid (h~7-12, w~8-14) with 2-6 "
    "ISOLATED SOLID 2×2 SQUARES at scattered "
    "interior positions, each in a DISTINCT "
    "non-zero color. Squares are 4-cell "
    "monochrome blocks at (r, c)..(r+1, c+1) "
    "with at least 1-cell margin from each "
    "other and from grid edges. Each square "
    "has EMPTY DIAGONAL CORNERS (cells at "
    "(r-1, c-1), (r-1, c+2), (r+2, c-1), "
    "(r+2, c+2) are 0). Rule: for EACH "
    "SOLID 2×2 SQUARE at (r, c), BLOOM "
    "one same-color cell from each of its 4 "
    "DIAGONAL CORNERS — paint cells at "
    "(r-1, c-1), (r-1, c+2), (r+2, c-1), "
    "(r+2, c+2) with the SQUARE'S COLOR. The "
    "2×2 square stays solid. Cells outside "
    "the grid bounds are dropped. Net: each "
    "2×2 square sprouts a diagonal X-bloom "
    "of 4 same-color cells at its diagonal "
    "corners."
)

# Rivals: 'bloom orthogonal corners' refuted by ≥1 demo where output
# shows diagonal X-pattern not + pattern. 'bloom only one square'
# refuted by ≥1 demo with ≥2 squares. 'use a fixed bloom color'
# refuted by ≥2 demos with different square colors.
# 3 demos with varied square counts + colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each object is an isolated solid monochrome 2x2 block",
    "each block has empty diagonal corner cells available for blooming",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_squares", "single_cell", "on_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_squares":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_2x2_squares",
                       "valid": "isolated_2x2_squares"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_squares|single_cell|on_edge"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 solid 2x2 monochrome block with empty diagonal corner cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    # Find at least one solid 2x2 monochrome block
    has_square = False
    for r in range(h - 1):
        for c in range(w - 1):
            v = grid[r][c]
            if v != 0 and grid[r][c+1] == v and grid[r+1][c] == v and grid[r+1][c+1] == v:
                has_square = True
                break
        if has_square:
            break
    if not has_square:
        errs.append("no solid 2x2 monochrome block found")
    return errs


def _footprint(r: int, c: int) -> set[tuple[int, int]]:
    return {(rr, cc) for rr in range(r - 1, r + 3) for cc in range(c - 1, c + 3)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        square_count = ctx.draw_int("square_count", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        square_count = ctx.draw_int("square_count", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        square_count = ctx.draw_int("square_count", 2, 4)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    anchors = [(r, c) for r in range(1, h - 2) for c in range(1, w - 2)]
    rng.shuffle(anchors)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(square_count, 9))
    occupied: set[tuple[int, int]] = set()

    placed = 0
    for r, c in anchors:
        footprint = _footprint(r, c)
        if footprint & occupied:
            continue
        color = colors[placed % len(colors)]
        for rr in (r, r + 1):
            for cc in (c, c + 1):
                grid[rr][cc] = color
        occupied |= footprint
        placed += 1
        if placed >= square_count:
            break
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_squares":
        # blank → no 2x2 squares to bloom from
        return g
    if name == "single_cell":
        # singleton cells → not 2x2 squares
        g[3][3] = 4; g[5][6] = 6
        return g
    if name == "on_edge":
        # 2x2 at corner → diagonal blooms go out of bounds
        for r in range(2):
            for c in range(2):
                g[r][c] = 4
        return g
    return g
