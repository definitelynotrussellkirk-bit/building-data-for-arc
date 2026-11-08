"""Generator for arc_puzzle_bank_21_set11_bundle:medium_k13 — Ray-fill from cells to 5-wall.

Rule: 5-col is divider. For each non-{0,5} cell on left, fill to right
with that color until just before wall.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_wall, cells_on_right_of_wall, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28268c57c367"
VERSION = "1.1.0"  # in=9: narrow 6-8 x 9-11. Wall-column rule reads rows/cols; widened grid.
TASK_ID = "28268c57c367"
SUMMARY = (
    "0-bg grid (h~6-8, w~9-11) with: (a) one full-height "
    "color-5 WALL column at col = wall (drawn ~2w/3 from "
    "left); (b) 2-4 isolated non-{0,5} SOURCE cells on the "
    "LEFT side (cols < wall), at distinct rows. Rule: "
    "detect the wall column (the unique full-5 col). For "
    "each non-{0, 5} cell (r, c) on the left side (c < "
    "wall), cast a RAY to the right: for cc from c+1 to "
    "wall-1, paint output[r][cc] with that source cell's "
    "color (only if currently 0). Net: each source cell "
    "emits a horizontal ray that stops just before the "
    "wall, filling the gap with its color."
)

INVARIANTS = [
    "exactly one full-column 5-wall",
    "between 2 and 4 sparse cells on left side, at distinct rows",
    "no cells on right side of wall",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_wall", "cells_on_right_of_wall", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "left_of_wall",
                       "valid": "left_of_wall"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # wall-column rule reads rows/cols; was 6-8 x 9-11 (in=9). Widen for shape variety.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 9, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 12, 18)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 10, 15)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    wall = rng.randint(w * 2 // 3, w - 2)
    for r in range(h):
        g[r][wall] = 5
    n = rng.randint(2, 4)
    rows = list(range(h)); rng.shuffle(rows)
    for i, r in enumerate(rows[:n]):
        color = rng.choice([2, 3, 4, 6, 7, 8, 9])
        c = rng.randint(0, wall - 2)
        g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_wall":
        # cells without a 5-wall → ray has no termination point
        g[1][2] = 4; g[3][1] = 6; g[5][3] = 7
        return g
    if name == "cells_on_right_of_wall":
        # cells on the right side of wall → wrong-side cells, ray goes off-grid
        wall = 4
        for r in range(h):
            g[r][wall] = 5
        g[2][wall + 1] = 4
        g[5][wall + 2] = 6
        return g
    if name == "no_cells":
        # wall present but no source cells → no rays to cast
        wall = 6
        for r in range(h):
            g[r][wall] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    wall_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(wall_cols) != 1:
        return [f"expected exactly one full-height color-5 wall, found {len(wall_cols)}"]
    wall = wall_cols[0]
    sources = [(r, c, grid[r][c]) for r in range(h) for c in range(wall) if grid[r][c] not in (0, 5)]
    if not (2 <= len(sources) <= 4):
        errors.append(f"expected 2-4 left source cells, found {len(sources)}")
    if len({r for r, _, _ in sources}) != len(sources):
        errors.append("source cells are not on distinct rows")
    if any(c >= wall - 1 for _, c, _ in sources):
        errors.append("a source has no blank gap before the wall")
    wrong_side = [(r, c) for r in range(h) for c in range(wall + 1, w) if grid[r][c] not in (0, 5)]
    if wrong_side:
        errors.append("non-wall source cells appear right of the wall")
    return errors
