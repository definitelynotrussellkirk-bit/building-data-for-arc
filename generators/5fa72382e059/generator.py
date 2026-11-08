"""Generator for arc_puzzle_bank_21_set8:medium_h11 — reflect across color-8 guide line.

Rule: color-8 cells form either a full row or a full column (the
"guide"). Reflect all non-{0,8} cells across that line: for a guide
row gr, cell at (r,c) maps to (2*gr - r, c); for a guide column gc,
cell at (r,c) maps to (r, 2*gc - c). Output is a fresh grid with only
the reflected cells; original positions and the 8-guide are dropped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5fa72382e059"
VERSION = "2.0.0"  # rewrite — was for completely wrong rule (gallery-pack)
TASK_ID = "5fa72382e059"

SUMMARY = (
    "Grid with: (a) a complete row OR complete column of color-8 "
    "cells (the 'guide line'); (b) one or more colored non-{0,8} "
    "cells on ONE side of the guide. Rule: detect the guide — if it's "
    "a full row at row gr, reflect non-guide non-bg cells across it "
    "by (r, c) → (2*gr - r, c). If it's a full column at col gc, "
    "reflect by (r, c) → (r, 2*gc - c). Output is a fresh 0-grid with "
    "only the reflected cells; the original cells and the 8-guide do "
    "NOT appear in the output. Reflected cells outside grid bounds "
    "are silently dropped."
)

# Rivals: 'output is input' refuted by demos (output drops 8s and
# input non-guide cells). 'preserve guide line' refuted by demos
# (output is 8-free). 'preserve original cells too (add reflection)'
# refuted by demos showing only the reflection. 'use color 8 in
# output' refuted by demos preserving original cell colors. 'reflect
# diagonally' refuted by demos showing row/col reflection only.
# 'rotate 180 around guide center' refuted by demos showing
# reflection, not rotation. 4 demos covering (row guide × col guide)
# × (cells before vs after the guide) pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one complete color-8 line (either a full row OR a full column, not both)",
    "≥1 non-{0,8} colored cell on ONE side of the guide line",
    "the guide line is NOT at the edge (so reflected cells have space)",
    "every non-guide cell's reflection across the guide line lands in-bounds (or close to)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_guide", "no_cells", "guide_at_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "guide_orient":   {"type": "str", "default": "rng row|col", "valid": "row|col"},
    "n_cells":        {"type": "int", "default": "rng 3..6", "valid": "1..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
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
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 6, 8)
        n_cells = ctx.draw_int("n_cells", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        n_cells = ctx.draw_int("n_cells", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 7, 11)
        n_cells = ctx.draw_int("n_cells", 3, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    orient = (overrides.get("guide_orient") or
              ctx.draw_choice("guide_orient", ["row", "col"]))
    colors = [1, 2, 3, 4, 5, 6, 7, 9]
    if orient == "row":
        # Guide row at some non-edge row.  Candidate placement is sampled from
        # cells whose reflection is known in-bounds; the old bounded retry loop
        # could exhaust on small easy grids and emit a guide with zero objects.
        gr = rng.randint(2, h - 3)
        for c in range(w):
            g[gr][c] = 8
        side = rng.choice(["above", "below"])
        if side == "above":
            rows = range(0, gr)
        else:
            rows = range(gr + 1, h)
        candidates = [(r, c) for r in rows for c in range(w)
                      if 0 <= 2 * gr - r < h]
        rng.shuffle(candidates)
        for r, c in candidates[:n_cells]:
            g[r][c] = rng.choice(colors)
    else:
        gc = rng.randint(2, w - 3)
        for r in range(h):
            g[r][gc] = 8
        side = rng.choice(["left", "right"])
        if side == "left":
            cols = range(0, gc)
        else:
            cols = range(gc + 1, w)
        candidates = [(r, c) for r in range(h) for c in cols
                      if 0 <= 2 * gc - c < w]
        rng.shuffle(candidates)
        for r, c in candidates[:n_cells]:
            g[r][c] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_guide":
        # cells but no 8-guide — rule has no reflection axis
        g[2][2] = 4
        g[5][6] = 6
        return g
    if name == "no_cells":
        # 8-guide but no cells to reflect — output is empty
        for c in range(w):
            g[3][c] = 8
        return g
    if name == "guide_at_edge":
        # Guide at row 0 — reflected cells go out of bounds
        for c in range(w):
            g[0][c] = 8
        g[3][2] = 4
        return g
    return g


def _guide_lines(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    return rows, cols


def self_check(grid, *, difficulty=None, meta=None):
    problems = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is not a nonempty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows are ragged"]
    guide_rows, guide_cols = _guide_lines(grid)
    if len(guide_rows) + len(guide_cols) != 1:
        problems.append("expected exactly one complete color-8 guide row or column")
        return problems
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    if not cells:
        problems.append("default path emitted a guide but no object cells to reflect")
        return problems
    if guide_rows:
        gr = guide_rows[0]
        if gr in (0, h - 1):
            problems.append("guide row should not be on the edge")
        above = any(r < gr for r, _ in cells)
        below = any(r > gr for r, _ in cells)
        if above and below:
            problems.append("object cells should be on one side of the guide row")
        if any(not (0 <= 2 * gr - r < h) for r, _ in cells):
            problems.append("an object cell reflects out of bounds")
    else:
        gc = guide_cols[0]
        if gc in (0, w - 1):
            problems.append("guide column should not be on the edge")
        left = any(c < gc for _, c in cells)
        right = any(c > gc for _, c in cells)
        if left and right:
            problems.append("object cells should be on one side of the guide column")
        if any(not (0 <= 2 * gc - c < w) for _, c in cells):
            problems.append("an object cell reflects out of bounds")
    return problems
