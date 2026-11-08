"""Generator for arc_additional_puzzles_21_set22_bundle:E149.

Rule: a small nonzero glyph is surrounded by blank rows and columns;
output is the bbox crop of all nonzero cells.

Combinatorial axes (8): grid_h/w, palette_kind, glyph_position,
palette_size, position_bias, n_distinct_colors, padding, texture.
Degenerates: glyph_at_edge, glyph_fills_grid, no_glyph.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c35effd8e6bc"
VERSION = "2.0.1"
TASK_ID = "c35effd8e6bc"
SUMMARY = (
    "0-bg grid (h~8-11, w~8-11) containing a small GLYPH in 2 "
    "distinct non-bg colors: a connected 5-cell motif "
    "(L-tetromino-like) in colors[0] plus 1 isolated cell of "
    "colors[1] placed near it. The glyph is fully interior — "
    "≥1 full blank row above/below AND ≥1 full blank col left/"
    "right. Rule: crop the grid to the bbox of all non-zero "
    "cells. Output = a small grid containing only the glyph."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "all nonzero cells are inside a smaller bounding box",
    "at least one full blank row above and below the glyph",
    "at least one full blank col left and right of the glyph",
    "glyph uses 2 distinct non-bg colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("glyph_at_edge", "glyph_fills_grid", "no_glyph")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..13"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "glyph_position": {"type": "str", "default": "interior",
                       "valid": "interior"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "interior",
                       "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "padding":        {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
    colors = list(ctx.draw_distinct_colors("colors", n=2, exclude=[0]))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Pick a random connected 4-6 cell motif via BFS-ish growth
    motif = [(0, 0)]
    seen = {(0, 0)}
    n_cells = rng.randint(4, 6)
    for _ in range(n_cells - 1):
        for _try in range(30):
            r, c = rng.choice(motif)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                motif.append((nr, nc))
                seen.add((nr, nc))
                break
    # Normalize motif to (0, 0)
    min_r = min(r for r, _ in motif)
    min_c = min(c for _, c in motif)
    motif = [(r - min_r, c - min_c) for r, c in motif]
    mh = max(r for r, _ in motif) + 1
    mw = max(c for _, c in motif) + 1
    # Pick an isolated single-cell offset (within bounds, not on motif)
    extra_dr = rng.randint(-1, mh)
    extra_dc = mw + rng.randint(1, 2)
    glyph_h = max(mh, extra_dr + 1) - min(0, extra_dr)
    glyph_w = max(mw, extra_dc + 1)
    if glyph_h >= h - 1 or glyph_w >= w - 1:
        # too big — fall back to original
        for dr, dc in [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)]:
            g[1 + dr][1 + dc] = colors[0]
        g[2][4] = colors[1]
        return g
    top = ctx.draw_int("top", 1, max(1, h - glyph_h - 1))
    left = ctx.draw_int("left", 1, max(1, w - glyph_w - 1))
    base_r = top - min(0, extra_dr)
    for dr, dc in motif:
        g[base_r + dr][left + dc] = colors[0]
    g[base_r + extra_dr][left + extra_dc] = colors[1]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Glyph uses >=2 nonzero colors; >=1 blank row above/below and >=1 blank col left/right."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nz_rows = [r for r in range(h) if any(grid[r][c] != 0 for c in range(w))]
    nz_cols = [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]
    if not nz_rows:
        return ["no nonzero cells found"]
    if nz_rows[0] == 0:
        errors.append("no blank row above glyph (glyph touches top edge)")
    if nz_rows[-1] == h - 1:
        errors.append("no blank row below glyph (glyph touches bottom edge)")
    if nz_cols[0] == 0:
        errors.append("no blank col left of glyph (glyph touches left edge)")
    if nz_cols[-1] == w - 1:
        errors.append("no blank col right of glyph (glyph touches right edge)")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errors.append(f"expected >=2 nonzero colors, found {len(colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "glyph_at_edge":
        # glyph touches grid edge — no blank padding to strip
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[dr][dc] = 4
        return g
    if name == "glyph_fills_grid":
        # nonzero in every row/col — bbox crop = full grid (rule no-op)
        for r in range(h):
            for c in range(w):
                g[r][c] = 4 if (r + c) % 2 == 0 else 0
        # ensure border rows/cols also have nonzero
        for r in range(h):
            g[r][0] = 5
            g[r][w - 1] = 5
        return g
    if name == "no_glyph":
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal-path invariant: nonzero glyph has blank margin and exactly two colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    nz = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        return ["no glyph"]
    errors = []
    rs = [r for r, _, _ in nz]; cs = [c for _, c, _ in nz]
    if min(rs) <= 0 or max(rs) >= h - 1:
        errors.append("glyph lacks a full blank row margin")
    if min(cs) <= 0 or max(cs) >= w - 1:
        errors.append("glyph lacks a full blank column margin")
    colors = {v for _, _, v in nz}
    if len(colors) != 2:
        errors.append(f"glyph uses {len(colors)} colors, expected 2")
    return errors
