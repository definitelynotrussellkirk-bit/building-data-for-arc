"""Generator for arc_additional_puzzles_21_set15_bundle:E105 — Shift non-(0,0) cells by code direction.

Rule: code at (0,0) ∈ {1: up, 2: right, 3: down, 4: left}. Output:
empty grid with each non-(0,0) cell shifted in that direction.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_code, code_out_of_range, cells_at_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "96e581ff27a4"
VERSION = "2.0.1"
TASK_ID = "96e581ff27a4"
SUMMARY = (
    "0-bg grid (h~5-7, w~7-9) with: (a) cell "
    "(0, 0) holding a DIRECTION CODE ∈ "
    "{1, 2, 3, 4} (1=up, 2=right, 3=down, "
    "4=left); (b) 2-3 INTERIOR CELLS placed at "
    "rows 1..h-2, cols 1..w-2 in distinct "
    "non-zero colors. Rule: READ the CODE at "
    "(0, 0) and determine shift vector "
    "(dr, dc): 1→(-1, 0), 2→(0, +1), "
    "3→(+1, 0), 4→(0, -1). Build an EMPTY "
    "OUTPUT GRID. For EVERY non-(0,0) cell, "
    "COMPUTE its shifted position (r+dr, "
    "c+dc) and PAINT that cell with the "
    "marker's value. The code cell is "
    "consumed. Net: code at origin dictates "
    "direction; marker cells shift uniformly "
    "by 1 cell in that direction."
)

INVARIANTS = [
    "(0,0) ∈ {1, 2, 3, 4}",
    "1-3 cells with values in 1..9 elsewhere (not at (0,0))",
    "shifted positions all in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_code", "cells_at_edge", "no_other_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "code_at_origin_with_interior_cells",
                       "valid": "code_at_origin_with_interior_cells"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: (0,0) is a direction code in {1,2,3,4}; ≥1 other non-bg cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    code = grid[0][0]
    if code not in (1, 2, 3, 4):
        errs.append(f"(0,0) expected direction code in {{1,2,3,4}}; got {code}")
    others = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
              if grid[r][c] != 0 and not (r == 0 and c == 0)]
    if not others:
        errs.append("no non-bg cells other than the code at (0,0)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 9)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    g[0][0] = rng.randint(1, 4)
    palette = [3, 4, 5, 6, 7, 8, 9]
    n = rng.randint(2, 3)
    placed = []
    for _ in range(40):
        if len(placed) >= n: break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if (r, c) not in placed and g[r][c] == 0:
            g[r][c] = rng.choice(palette)
            placed.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_code":
        # (0,0) is 0 → no direction code, rule has no operation defined
        g[2][3] = 6; g[3][5] = 7
        return g
    if name == "cells_at_edge":
        # cells already at the relevant edge → shift would push them out of bounds
        g[0][0] = 1   # code: up
        g[0][3] = 6   # already at top, can't shift up
        g[1][5] = 7   # near top
        return g
    if name == "no_other_cells":
        # only the code cell, no other cells → nothing to shift
        g[0][0] = 2
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    code = grid[0][0]
    dirs = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
    if code not in dirs:
        return ["cell (0,0) must be a direction code in 1..4"]
    dr, dc = dirs[code]
    movers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
              if v != 0 and (r, c) != (0, 0)]
    if len(movers) < 2:
        errors.append("need at least two shifted marker cells")
    for r, c in movers:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w):
            errors.append("a marker would shift out of bounds")
            break
    return errors
