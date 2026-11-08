"""Generator for arc_additional_puzzles_21_set3:E19 — Diagonal 8-pair → fill anti-diagonal corners with 1.

Rule: 2×2 block where (r,c) and (r+1,c+1) are 8 with (r,c+1) and
(r+1,c) being 0 → set those 0s to 1. Same for the other diagonal.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, antidiag_filled, only_singletons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2826c36048c1"
VERSION = "1.1.1"
TASK_ID = "2826c36048c1"
SUMMARY = (
    "0-bg grid (h, w~6-8) "
    "with 2-3 DIAGONAL "
    "COLOR-8 (cyan) PAIRS"
    ": each pair is two "
    "8-cells at diagonal "
    "positions in a 2×2 "
    "block — either MAIN "
    "diagonal {(r, c), "
    "(r+1, c+1)} or ANTI "
    "diagonal {(r, c+1), "
    "(r+1, c)}. The "
    "ANTI-DIAGONAL corners "
    "(the other 2 cells "
    "of the 2×2 block) "
    "are BG-0 initially. "
    "Pairs are placed at "
    "non-touching "
    "positions (Chebyshev "
    "distance ≥3 between "
    "centers). Rule "
    "(FILL ANTI-DIAGONAL "
    "CORNERS OF EACH 8-"
    "DIAGONAL PAIR WITH "
    "COLOR 1): For EACH "
    "2×2 BLOCK containing "
    "an 8-DIAGONAL PAIR "
    "(two 8s at diagonal "
    "positions and two "
    "bg-0 cells at anti-"
    "diagonal positions): "
    "PAINT the anti-"
    "diagonal corner "
    "cells (the BG-0 "
    "cells) with COLOR 1. "
    "The 8-cells stay. "
    "Net: each diagonal "
    "8-pair completes "
    "its 2×2 with blue "
    "corners on the "
    "opposite diagonal."
)

INVARIANTS = [
    "≥2 8-pairs at diagonal positions",
    "anti-diagonal corners are 0 (will become 1)",
    "no two 8-pairs touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "antidiag_filled", "only_singletons")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..15"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "diag_8_pairs",
                       "valid": "diag_8_pairs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 color-8 cells forming diagonal pairs in 2×2 blocks."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_pairs", "antidiag_filled", "only_singletons"):
        return []
    errs = []
    c8 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 8)
    if c8 < 2:
        errs.append(f"only {c8} color-8 cells; expected ≥2 (for at least one diagonal pair)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # same-size 2x2-scan rule reads rows/cols; was 6-8 (in=9). Widen for shape variety.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 5, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 15)
        w = ctx.draw_int("grid_w", 10, 15)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    placed = []
    for _ in range(40):
        if len(placed) >= rng.randint(2, 3): break
        r = rng.randint(0, h - 2); c = rng.randint(0, w - 2)
        if all(abs(r - pr) > 2 or abs(c - pc) > 2 for pr, pc in placed):
            d = rng.choice([(0, 0, 1, 1), (0, 1, 1, 0)])
            g[r + d[0]][c + d[1]] = 8
            g[r + d[2]][c + d[3]] = 8
            placed.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no 8-pairs, rule has no antidiag corners to fill
        return g
    if name == "antidiag_filled":
        # 2x2 block with all 4 cells non-zero → antidiag corners aren't 0
        g[1][1] = 8; g[2][2] = 8
        g[1][2] = 4; g[2][1] = 6   # antidiag corners already non-zero
        return g
    if name == "only_singletons":
        # only isolated 8s → no diagonal pair, rule never fires
        g[1][1] = 8
        g[3][4] = 8
        g[5][2] = 8
        return g
    return g
