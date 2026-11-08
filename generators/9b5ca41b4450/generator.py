"""Generator for arc_additional_puzzles_21_set17_bundle:E114.

Rule: take the first 2 non-zero cells (same color); paint the
rectangle outline between them on a blank canvas.

Combinatorial axes (8): grid_h, grid_w, palette_kind, bbox_size,
palette_size, position_bias, n_distinct_colors, rect_aspect, texture.
Degenerates: no_cells, single_cell, three_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9b5ca41b4450"
VERSION = "1.1.1"
TASK_ID = "9b5ca41b4450"
SUMMARY = "Exactly 2 cells of one color, both at non-trivial bbox corners."

INVARIANTS = [
    "exactly 2 non-zero cells, same color",
    "the 2 cells are at distinct rows AND distinct cols",
    "the bbox is ≥3×3",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_cells", "single_cell", "three_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "bbox_size":      {"type": "str", "default": "rng", "valid": "rng"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "diag_corners", "valid": "diag_corners"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "rect_aspect":    {"type": "str", "default": "rng", "valid": "rng"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    r0 = rng.randint(0, h - 4); c0 = rng.randint(0, w - 4)
    r1 = rng.randint(r0 + 2, h - 1)
    c1 = rng.randint(c0 + 2, w - 1)
    g[r0][c0] = color
    g[r1][c1] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_cells":
        # empty grid — no corner cells, so no rectangle to draw
        return g
    if name == "single_cell":
        # one cell only → predicate "exactly 2" fails; bbox degenerate
        g[2][3] = 5
        return g
    if name == "three_cells":
        # three same-color cells → which 2 corners? Selection ambiguous
        g[1][1] = 4; g[5][6] = 4; g[3][2] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: exactly 2 nonzero cells; same color; distinct rows and cols; bbox >=3x3."""
    msgs = []
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(cells) != 2:
        msgs.append(f"expected exactly 2 nonzero cells, got {len(cells)}")
        return msgs
    (r0, c0), (r1, c1) = cells
    if grid[r0][c0] != grid[r1][c1]:
        msgs.append(f"the 2 cells have different colors ({grid[r0][c0]} vs {grid[r1][c1]})")
    if r0 == r1:
        msgs.append("the 2 cells share the same row (bbox must span >=2 rows)")
    if c0 == c1:
        msgs.append("the 2 cells share the same column (bbox must span >=2 cols)")
    if abs(r1 - r0) < 2 or abs(c1 - c0) < 2:
        msgs.append(f"bbox is too small: rows span {abs(r1-r0)+1}, cols span {abs(c1-c0)+1} (need >=3x3)")
    return msgs
