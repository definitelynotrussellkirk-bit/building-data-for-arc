"""Generator for arc_additional_puzzles_21_set22_bundle:E153.

Rule: take all non-bg cells (single color); compute bbox; output draws
2 diagonals of that color: top-left to bottom-right, and top-right
to bottom-left, of bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, bbox_side,
palette_size, position_bias, n_distinct_colors, rect_aspect, texture.
Degenerates: no_cells, single_cell, non_square_bbox.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6ebcd82f8e83"
VERSION = "2.0.1"
TASK_ID = "6ebcd82f8e83"
SUMMARY = (
    "0-bg grid (h, w~5-16) "
    "with 2-4 CELLS of a "
    "SINGLE NON-BG COLOR "
    "from {1..9} placed "
    "at the CORNERS of a "
    "SQUARE BBOX (side "
    "3-min(h, w)-2, "
    "height == width). "
    "Always anchors at "
    "(r1, c1) and "
    "(r1+side, c1+side) "
    "with 50% chance of "
    "anti-diagonal "
    "corners (r1, c1+"
    "side) and "
    "(r1+side, c1) also "
    "set. Rule (DRAW X "
    "ACROSS SQUARE BBOX "
    "IN ORIGINAL COLOR): "
    "identify the 2+ "
    "NON-BG CELLS (all "
    "same color). "
    "COMPUTE their bbox "
    "(r1, c1, r2, c2) "
    "which is SQUARE "
    "(r2-r1 == c2-c1). "
    "EMIT a FRESH h×w "
    "OUTPUT GRID. PAINT "
    "BOTH DIAGONALS of "
    "the bbox in the "
    "ORIGINAL color — "
    "TL→BR diagonal AND "
    "TR→BL diagonal, "
    "forming an X. Off-"
    "diagonal cells "
    "stay 0. Net: 2-4 "
    "corner markers "
    "become an X "
    "spanning their "
    "square bbox."
)

# Rivals: 'output is input' refuted by demos (X is drawn).
# 'one diagonal only' refuted by demos with full X. 'paint entire
# bbox' refuted by demos with off-diagonal cells staying 0. 'recolor
# to 8' refuted by demos preserving input color. 3 demos with
# varied bbox sizes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly 2 cells of a single non-bg color",
    "bbox is square (r2-r1 == c2-c1)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_cells", "single_cell", "non_square_bbox")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "bbox_side":      {"type": "int", "default": "rng 2..min(h,w)-3",
                       "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "diag_corners", "valid": "diag_corners"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "rect_aspect":    {"type": "str", "default": "square", "valid": "square"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 1 non-zero color; ≥2 cells; bbox is square; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(cells) < 2:
        errs.append(f"expected ≥2 non-zero cells, found {len(cells)}")
        return errs
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1:
        errs.append(f"expected exactly 1 non-zero color, found {colors}")
    r1 = min(r for r, c in cells); r2 = max(r for r, c in cells)
    c1 = min(c for r, c in cells); c2 = max(c for r, c in cells)
    if (r2 - r1) != (c2 - c1):
        errs.append(f"bbox not square: rows {r1}-{r2} vs cols {c1}-{c2}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(5, 7); w = rng.randint(5, 8)
    elif difficulty == "hard":
        h = rng.randint(11, 16); w = rng.randint(11, 16)
    else:
        h = rng.randint(7, 11); w = rng.randint(8, 12)
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    side = rng.randint(3, min(h, w) - 2)
    r1 = rng.randint(0, h - side - 1); c1 = rng.randint(0, w - side - 1)
    # Place 2-4 cells of the bbox so that the bbox of these cells is the
    # full r1..r1+side, c1..c1+side. Always anchor at the 4 corners; we
    # can add interior cells too.
    g[r1][c1] = color
    g[r1 + side][c1 + side] = color
    # Sometimes also add the other 2 corners
    if rng.random() < 0.5:
        g[r1][c1 + side] = color
    if rng.random() < 0.5:
        g[r1 + side][c1] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_cells":
        # empty grid — no bbox, no diagonals
        return g
    if name == "single_cell":
        # only 1 cell → bbox is degenerate (1×1), diagonals collapse
        g[3][4] = 5
        return g
    if name == "non_square_bbox":
        # 2 cells with non-square bbox → "square bbox" predicate fails; X uneven
        g[1][1] = 4
        g[3][6] = 4
        return g
    return g
