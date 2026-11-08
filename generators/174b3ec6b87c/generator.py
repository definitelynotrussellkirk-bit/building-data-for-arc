"""Generator for additional_scaffolded:E1.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, full_2x2_filled, single_diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "174b3ec6b87c"
VERSION = "2.0.1"
TASK_ID = "174b3ec6b87c"
SUMMARY = (
    "0-bg grid (h, w~7-12) with 2-5 separated 2×2 "
    "WINDOWS, each containing TWO color-3 (green) "
    "cells on a DIAGONAL — either the main diagonal "
    "((0,0) + (1,1)) or the anti-diagonal "
    "((0,1) + (1,0)) — and the other two cells empty "
    "(0). Windows are 4-conn isolated (≥ 3 cells "
    "apart). Rule: for every 2×2 window whose two "
    "diagonal cells are color 3 and the other two are "
    "0, PAINT the two empty corners with color 7 "
    "(orange) to complete the 2×2 with the diagonal 3s "
    "and the anti-diagonal 7s. The color-3 cells stay. "
    "Net: each diagonal-pair window becomes a "
    "checkerboard 2×2 with 3 on one diagonal and 7 on "
    "the other."
)

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has two diagonal 3 cells and two empty cells",
    "active windows are separated so their local completions do not overlap",
    "both diagonal orientations can appear",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "full_2x2_filled", "single_diagonal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_diagonal_pairs",
                       "valid": "separated_diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, only color-3 non-bg cells, at least one pair of 3-cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_pairs", "full_2x2_filled", "single_diagonal"):
        return errs
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    others = [(r, c) for r in range(h) for c in range(w)
              if grid[r][c] not in (0, 3)]
    if not threes:
        errs.append("no color-3 cells for diagonal pairs")
    if others:
        errs.append(f"unexpected non-0 non-3 cells: {others[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_pairs = ctx.draw_int("n_pairs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_pairs = ctx.draw_int("n_pairs", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchors: list[tuple[int, int]] = []
    for _ in range(180):
        if len(anchors) >= n_pairs:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        if rng.choice([False, True]):
            g[r][c] = 3
            g[r + 1][c + 1] = 3
        else:
            g[r][c + 1] = 3
            g[r + 1][c] = 3
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 3
        g[2][2] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal pairs to complete
        return g
    if name == "full_2x2_filled":
        # 2x2 window already fully filled with 3 → no empty cells to receive 7
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 3
        return g
    if name == "single_diagonal":
        # only one cell of the diagonal pair → "two diagonal 3 cells" precondition fails
        g[1][1] = 3  # missing (2,2)
        g[4][5] = 3
        return g
    return g
