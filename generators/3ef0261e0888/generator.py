"""Generator for arc_additional_puzzles_21_set9:M58 — Extract values at row/col-marker intersections.

Rule:
  - rs = rows where col 0 has value 8 (rows 1+)
  - cs = cols where row 0 has value 8 (cols 1+)
  - Output: 2D grid of values at (r, c) for r in rs, c in cs.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rows, n_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_row_markers, no_col_markers, blank_interior.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ef0261e0888"
VERSION = "1.2.0"
TASK_ID = "3ef0261e0888"
SUMMARY = "8-markers in row 0 and col 0; output is values at marker-row × marker-col intersections."

INVARIANTS = [
    "between 1 and 3 cols (in row 0) marked with 8",
    "between 1 and 3 rows (in col 0) marked with 8",
    "non-marker cells in interior have varied non-zero, non-8 values",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_row_markers", "no_col_markers", "blank_interior")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rows":         {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_cols":         {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 4..7", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "row0_col0_markers",
                       "valid": "row0_col0_markers"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..7", "valid": "2..8"},
    "density":        {"type": "str", "default": "framed", "valid": "framed"},
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
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 5, 6)
        n_rows = ctx.draw_int("n_rows", 1, min(2, h - 1))
        n_cols = ctx.draw_int("n_cols", 1, min(2, w - 1))
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        n_rows = ctx.draw_int("n_rows", 3, min(3, h - 1))
        n_cols = ctx.draw_int("n_cols", 3, min(3, w - 1))
    else:
        h = ctx.draw_int("grid_h", 4, 7)
        w = ctx.draw_int("grid_w", 5, 8)
        n_rows = ctx.draw_int("n_rows", 1, min(3, h - 1))
        n_cols = ctx.draw_int("n_cols", 1, min(3, w - 1))
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    for r in range(1, h):
        for c in range(1, w):
            g[r][c] = color_rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    cols = list(range(1, w)); rng.shuffle(cols)
    for c in cols[:n_cols]: g[0][c] = 8
    rows = list(range(1, h)); rng.shuffle(rows)
    for r in rows[:n_rows]: g[r][0] = 8
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 6
    g = full_grid(h, w, 0)
    if name == "no_row_markers":
        # only col-markers, no row-markers → intersection set is empty
        for r in range(1, h):
            for c in range(1, w):
                g[r][c] = ((r + c) % 7) + 1
        for c in [2, 4]: g[0][c] = 8
        return g
    if name == "no_col_markers":
        # only row-markers, no col-markers → intersection set is empty
        for r in range(1, h):
            for c in range(1, w):
                g[r][c] = ((r + c) % 7) + 1
        for r in [1, 3]: g[r][0] = 8
        return g
    if name == "blank_interior":
        # markers present but interior all bg → output sub-matrix is all 0
        for c in [2, 4]: g[0][c] = 8
        for r in [1, 3]: g[r][0] = 8
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(1, h) if grid[r][0] == 8]
    cols = [c for c in range(1, w) if grid[0][c] == 8]
    if grid[0][0] != 0:
        msgs.append("corner (0,0) should stay background")
    if not (1 <= len(rows) <= 3):
        msgs.append(f"expected 1..3 row markers, got {len(rows)}")
    if not (1 <= len(cols) <= 3):
        msgs.append(f"expected 1..3 column markers, got {len(cols)}")
    if any(grid[r][0] not in (0, 8) for r in range(1, h)):
        msgs.append("column 0 contains non-marker payload")
    if any(grid[0][c] not in (0, 8) for c in range(1, w)):
        msgs.append("row 0 contains non-marker payload")
    interior = [grid[r][c] for r in range(1, h) for c in range(1, w)]
    if not interior or any(v in (0, 8) for v in interior):
        msgs.append("interior should be fully populated with nonzero, non-8 colors")
    hits = [grid[r][c] for r in rows for c in cols]
    if hits and any(v in (0, 8) for v in hits):
        msgs.append("row/column marker intersections include background or marker color")
    if len(set(interior)) < 2:
        msgs.append("interior palette collapsed to a single color")
    return msgs
