"""Generator for arc_puzzle_bank_21_set15_bundle:easy_o02.

Rule: four diagonal neighbors agree on one color around a zero center.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_xs, partial_xs, mixed_corner_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad92d10d919c"
VERSION = "2.0.1"
TASK_ID = "ad92d10d919c"
SUMMARY = (
    "0-bg grid (h~6-16, w~"
    "7-18) with 1-8 X-"
    "SHAPED MOTIFS — each "
    "motif places 4 SAME-"
    "COLOR cells at the "
    "DIAGONAL NEIGHBORS "
    "(r-1, c-1), (r-1, "
    "c+1), (r+1, c-1), "
    "(r+1, c+1) of an "
    "interior CENTER cell "
    "(r, c), with the "
    "center cell staying "
    "0. Each motif's "
    "color is DISTINCT "
    "from {1..9}. Motif "
    "3×3 neighborhoods "
    "are separated. Rule "
    "(DIAGONAL CONSENSUS "
    "FILL): For EACH "
    "INTERIOR 0-CELL (r, "
    "c): check its 4 "
    "DIAGONAL NEIGHBORS — "
    "if ALL ARE THE SAME "
    "NON-ZERO COLOR v, "
    "FILL (r, c) with v. "
    "X-motif centers "
    "satisfy this and "
    "become v. Other 0-"
    "cells stay 0. Net: "
    "each X-motif's "
    "center fills with "
    "its motif color."
)

# Rivals: 'output is input' refuted by demos (X centers fill).
# 'fill ALL 0-cells with same diagonals' is the rule; refuted only
# by non-X demos with mixed diagonals. 'fill cardinal-neighbor
# consensus' refuted by demos where diagonal consensus fills but
# cardinal doesn't. 'use color 8 for center' refuted by demos
# preserving the motif's color. 3 demos with ≥2 distinct-color X
# motifs cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each motif has four same-color diagonal cells around a zero center",
    "motif 3x3 neighborhoods are separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_xs", "partial_xs", "mixed_corner_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_count":    {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_diagonals",
                       "valid": "spaced_diagonals"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_xs|partial_xs|mixed_corner_colors"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one nonzero cell (diagonal motif corners)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_xs",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not has_nonzero:
        errs.append("no nonzero diagonal-motif cells found")
    return errs


def _neighborhood(r, c):
    return {(rr, cc) for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        motif_count = ctx.draw_int("motif_count", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        motif_count = ctx.draw_int("motif_count", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        motif_count = ctx.draw_int("motif_count", 3, 5)
    colors = ctx.draw_distinct_colors("colors", n=motif_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    occupied = set()
    for color in colors:
        for _ in range(300):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            block = _neighborhood(r, c)
            if not (block & occupied):
                for rr, cc in [(r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)]:
                    g[rr][cc] = color
                occupied |= block
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_xs":
        # blank grid → no diagonal-consensus motifs, rule has no centers to fill
        return g
    if name == "partial_xs":
        # only 3 of 4 diagonal corners set → predicate fails, no center fills
        # missing top-right corner around (3, 3)
        for (r, c) in [(2, 2), (4, 2), (4, 4)]: g[r][c] = 4   # missing (2, 4)
        # missing bottom-right corner around (5, 6)
        for (r, c) in [(4, 5), (4, 7), (6, 5)]: g[r][c] = 6   # missing (6, 7)
        return g
    if name == "mixed_corner_colors":
        # 4 diagonal corners present but with mixed colors → predicate "all same color" fails
        for (r, c, col) in [(2, 2, 4), (2, 4, 6), (4, 2, 4), (4, 4, 4)]: g[r][c] = col
        return g
    return g
