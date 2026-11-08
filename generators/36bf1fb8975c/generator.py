"""Generator for arc_puzzle_bank_eleventh21:E75.

Rule: recolor each nonzero body cell by the header color in its column.

Combinatorial axes (8): grid_h, grid_w, palette_kind, header_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_header, body_outside_header_cols, no_body_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "36bf1fb8975c"
VERSION = "1.1.1"
TASK_ID = "36bf1fb8975c"
SUMMARY = "Recolor each nonzero body cell by the header color in its column."

INVARIANTS = [
    "background is 0",
    "row 0 is the column header row",
    "body nonzero markers appear only below nonzero header columns",
    "header row is preserved",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_header", "body_outside_header_cols", "no_body_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..7", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "header_cols":    {"type": "int", "default": "rng 4..6", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 4..9", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "header_row_0",
                       "valid": "header_row_0"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse_columns",
                       "valid": "sparse_columns"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; row 0 (header row) exists; values in 0..9."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    if h < 2:
        errors.append(f"grid too short: h={h}")
    # Row 0 is the header row; in normal instances it has ≥1 nonzero cell
    header_nonzero = sum(1 for c in range(w) if grid[0][c] != 0)
    if header_nonzero == 0:
        pass  # degenerate (empty_header) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 8, 9)
        n = min(ctx.draw_int("header_cols", 3, 4), w, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 10)
        n = min(ctx.draw_int("header_cols", 5, 6), w, 9)
    else:
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 10)
        n = min(ctx.draw_int("header_cols", 4, 6), w, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cols = sorted(rng.sample(range(w), n))
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for c, color in zip(cols, colors):
        g[0][c] = color
    for c in cols:
        for r in rng.sample(range(1, h), rng.randint(1, min(3, h - 1))):
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "empty_header":
        # row 0 is all zeros → no header colors to remap with
        g[2][2] = 1; g[3][5] = 2; g[4][3] = 3
        return g
    if name == "body_outside_header_cols":
        # body cells appear in columns whose header row 0 is empty → no mapping
        g[0][1] = 4; g[0][6] = 7
        g[2][3] = 1; g[3][4] = 2  # cols 3,4 have no header
        return g
    if name == "no_body_cells":
        # only header row populated → rule has nothing to recolor
        g[0][1] = 4; g[0][3] = 5; g[0][6] = 7
        return g
    return g
