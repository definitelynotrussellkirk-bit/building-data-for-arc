"""Generator for arc_additional_puzzles_21_set7:E49 — Connect cells with L-paths.

Rule: for each color, find its cells in scan order. Draw L-paths between
consecutive cells (horizontal then vertical).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_cell_per_color, all_collinear, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "84fd4bcdc53c"
VERSION = "2.1.1"  # QUALITY: scale complexity (not just size) by difficulty; richer multi-path hard cases
TASK_ID = "84fd4bcdc53c"
SUMMARY = (
    "0-bg grid (easy ~8x10 -> hard up to ~19x20) with 1-4 distinct non-bg "
    "colors (scaled by difficulty), each with 2-4 ENDPOINT cells placed at "
    "DISTINCT rows AND distinct cols (so consecutive "
    "endpoints define a clear L-bend). Rule: for each "
    "color, sort its cells in scan order (row-major). "
    "Connect consecutive cells with an L-PATH: first "
    "horizontal segment from (r1, c1) to (r1, c2), then "
    "vertical segment from (r1, c2) to (r2, c2). Paint "
    "every cell along the L-path with that color. Net: "
    "endpoints become connected by staircase L-paths."
)

INVARIANTS = [
    "1-4 distinct non-bg colors (scaled by difficulty)",
    "each color: 2-4 cells, none on the same row or col",
    "no two cells (any colour) share a position",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_cell_per_color", "all_collinear", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..19 by difficulty", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..20 by difficulty", "valid": "7..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_colors":       {"type": "int", "default": "1 easy / 2 med / 3-4 hard", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "distinct_rows_cols",
                       "valid": "distinct_rows_cols"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|single_cell_per_color|all_collinear|no_cells"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 nonzero color; for each color its cells have distinct rows and distinct cols."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    from collections import defaultdict
    by_color = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                by_color[grid[r][c]].append((r, c))
    if not by_color:
        return []  # no_cells degenerate — allowed
    errs = []
    for color, cells in by_color.items():
        rows = [r for r, c in cells]
        cols = [c for r, c in cells]
        if len(rows) != len(set(rows)):
            errs.append(f"color {color}: cells share rows {rows} (expected distinct rows)")
        if len(cols) != len(set(cols)):
            errs.append(f"color {color}: cells share cols {cols} (expected distinct cols)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # difficulty scales COMPLEXITY (colors x cells-per-color = path count), not just size
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 11)
        n_colors, cell_lo, cell_hi = 1, 2, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 19)
        w = ctx.draw_int("grid_w", 14, 20)
        n_colors, cell_lo, cell_hi = rng.randint(3, 4), 2, 4
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 10, 14)
        n_colors, cell_lo, cell_hi = 2, 2, 3
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], min(n_colors, 8))
    occupied = set()
    for color in palette:
        n_cells = min(rng.randint(cell_lo, cell_hi), h, w)
        rows = rng.sample(range(h), n_cells)   # distinct rows + cols -> clean L-bends
        cols = rng.sample(range(w), n_cells)
        reserved_cols = set(cols)
        for r, c in zip(rows, cols):
            if (r, c) in occupied:
                # Keep every sampled endpoint. Reserve the other planned columns
                # while relocating this one, so later endpoints stay distinct.
                reserved_cols.remove(c)
                available_cols = [
                    candidate for candidate in range(w)
                    if candidate not in reserved_cols and (r, candidate) not in occupied
                ]
                # At most three earlier colors occupy this row. The supported
                # widths leave room after reserving this color's other columns.
                c = rng.choice(available_cols)
                reserved_cols.add(c)
            g[r][c] = color
            occupied.add((r, c))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "single_cell_per_color":
        # each color has only one cell → no consecutive pairs to L-connect
        g[2][3] = 4
        g[5][7] = 6
        return g
    if name == "all_collinear":
        # cells share a row → L-paths collapse to straight horizontal lines
        g[2][1] = 4
        g[2][5] = 4
        g[2][8] = 4
        return g
    if name == "no_cells":
        # empty grid → rule has nothing to connect
        return g
    return g
