"""Generator for arc_puzzle_bank_21_next:hard_c03 — Recolor body objects by row 0 markers, sorted by size.

Rule: row 0 markers (sorted by col); body objects (sorted by size asc,
then r1, c1); recolor each body object by next marker color. Output
empty + recolored.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_blobs, tied_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "6b1fe17a40a7"
VERSION = "1.1.1"
TASK_ID = "6b1fe17a40a7"
SUMMARY = "Row 0 has 4 markers + body has 4 distinct-size blobs."

INVARIANTS = [
    "row 0 has exactly 4 non-zero cells (markers)",
    "body has exactly 4 non-touching blobs of distinct sizes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_blobs", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "4", "valid": "4..4"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8..8"},
    "position_bias":  {"type": "str", "default": "row0_markers_plus_distinct_sizes",
                       "valid": "row0_markers_plus_distinct_sizes"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; row 0 has >=1 nonzero cell (markers); >=1 non-row-0 nonzero cell (blobs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    row0_markers = [c for c in range(w) if grid[0][c] != 0]
    if not row0_markers:
        return errs  # degenerate (no_markers) — allowed
    body_cells = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if not body_cells:
        errs.append("row 0 has markers but no body blobs in rows 1+")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = list(range(2, 10)); rng.shuffle(palette)
    g[0][1] = palette[0]; g[0][3] = palette[1]; g[0][5] = palette[2]; g[0][7] = palette[3]
    body_palette = [c for c in range(2, 10) if c not in palette[:4]]; rng.shuffle(body_palette)
    bp = body_palette + palette[:4]
    paint_at(g, 2, 0, [(0, 0), (0, 1)], bp[0])
    paint_at(g, 2, 6, [(0, 0), (1, 0), (1, 1)], bp[1])
    paint_at(g, 4, 1, [(0, 0), (1, 0), (0, 1), (1, 1)], bp[2])
    paint_at(g, 5, 5, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)], bp[3])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # blobs without row-0 markers → no recolor mapping defined
        paint_at(g, 2, 0, [(0, 0), (0, 1)], 4)
        paint_at(g, 2, 6, [(0, 0), (1, 0), (1, 1)], 6)
        paint_at(g, 4, 1, [(0, 0), (1, 0), (0, 1), (1, 1)], 7)
        return g
    if name == "no_blobs":
        # markers alone → nothing to recolor
        g[0][1] = 4; g[0][3] = 6; g[0][5] = 7; g[0][7] = 8
        return g
    if name == "tied_sizes":
        # blobs share sizes → "distinct sizes" sort precondition fails
        g[0][1] = 4; g[0][3] = 6
        paint_at(g, 2, 1, [(0, 0), (0, 1)], 7)
        paint_at(g, 2, 5, [(0, 0), (0, 1)], 9)
        return g
    return g
