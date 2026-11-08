"""Generator for arc_puzzle_bank_fifteenth21:E99 — connect horizontal endpoint pairs.

Rule: for each row with 2 same-color endpoints, fill the span between
them with that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d6f0c0336ec6"
VERSION = "2.0.1"  # adds executable self_check for horizontal endpoint-pair invariants
TASK_ID = "d6f0c0336ec6"
SUMMARY = (
    "0-bg grid (h~7-9, w~7-10) with 2-4 "
    "HORIZONTAL ENDPOINT PAIRS — each pair "
    "is 2 same-color cells in the SAME ROW "
    "at columns (c1, c2) with c2 ≥ c1 + 2 "
    "(gap of ≥1 bg cell between them). "
    "Each pair uses a DISTINCT non-zero "
    "color. Pairs occupy DISTINCT ROWS. "
    "Cells between endpoints start as 0. "
    "Rule: for EACH ROW that contains "
    "EXACTLY 2 SAME-COLOR CELLS, FILL the "
    "ENTIRE SPAN between them (all cells "
    "at columns min_c..max_c in that row) "
    "with the PAIR's COLOR. The two "
    "endpoints stay; the 0 cells between "
    "become the same color. Net: each "
    "same-color horizontal endpoint pair "
    "becomes a solid horizontal line "
    "connecting them."
)

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "same-color endpoint pairs share a row",
    "cells between endpoints are initially zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_endpoint_pairs",
                       "valid": "row_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|mismatched_endpoints|span_already_filled"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=target)
    used_rows: set[int] = set()
    placed = 0
    for _ in range(200):
        if placed >= target:
            break
        r = rng.randrange(h)
        if r in used_rows:
            continue
        c1 = rng.randint(0, w - 3)
        c2 = rng.randint(c1 + 2, w - 1)
        color = colors[placed]
        g[r][c1] = color
        g[r][c2] = color
        used_rows.add(r)
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate default samples for the horizontal bridge rule."""
    errs: list[str] = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        errs.append(f"grid exceeds ARC bounds: {h}x{w}")
    vals = [v for row in grid for v in row]
    if any(not isinstance(v, int) or v < 0 or v > 9 for v in vals):
        errs.append("grid contains non-ARC color values")
    colors = sorted({v for v in vals if v != 0})
    min_pairs = 3 if difficulty == "hard" else 2
    if len(colors) < min_pairs:
        errs.append(f"expected at least {min_pairs} endpoint-pair colors, found {len(colors)}")
    rows_seen: set[int] = set()
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if len(cells) != 2:
            errs.append(f"color {color} should appear exactly twice as endpoints, found {len(cells)} cells")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 != r2:
            errs.append(f"color {color} endpoints are not horizontal: {cells}")
            continue
        if abs(c2 - c1) < 2:
            errs.append(f"color {color} endpoints need at least one zero between them: {cells}")
            continue
        a, b = sorted((c1, c2))
        if any(grid[r1][c] != 0 for c in range(a + 1, b)):
            errs.append(f"color {color} bridge span is not initially empty")
        if r1 in rows_seen:
            errs.append(f"multiple endpoint-pair colors share row {r1}")
        rows_seen.add(r1)
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only → no pair to connect
        g[1][2] = 4
        g[3][6] = 6
        return g
    if name == "mismatched_endpoints":
        # endpoints with different colors → "same-color pair" precondition fails
        g[1][1] = 4; g[1][6] = 6   # mismatched
        g[3][2] = 3; g[3][7] = 7   # mismatched
        return g
    if name == "span_already_filled":
        # span between endpoints already non-zero → no empty cells to fill
        for c in range(1, 6): g[1][c] = 4    # full row
        g[3][1] = 6; g[3][3] = 9; g[3][5] = 6  # midpoint already non-zero
        return g
    return g
