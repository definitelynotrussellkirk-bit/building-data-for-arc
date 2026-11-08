"""Generator for arc_additional_puzzles_21_set9:E58 — Draw diagonal between same-color pairs.

Rule: for each color appearing exactly twice, if the two cells are
diagonal (|dr|=|dc|), draw a diagonal line between them in that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, axis_aligned_pair, single_endpoint.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "366ce015cd2a"
VERSION = "2.1.0"  # +self_check
TASK_ID = "366ce015cd2a"
SUMMARY = (
    "0-bg grid (h ∈ 7-10, w ∈ 7-10) "
    "with: N_PAIRS ∈ 2-3 DIAGONAL "
    "ENDPOINT PAIRS — each pair "
    "consists of 2 cells of the SAME "
    "non-bg color (colors drawn "
    "WITHOUT REPLACEMENT from "
    "{1,2,3,4,6,7,8,9}), placed at "
    "endpoints of a 45° diagonal of "
    "LENGTH k ∈ 2-4 cells: A = "
    "(r1, c1) and B = (r1+k*sr, "
    "c1+k*sc) where sr, sc ∈ {-1, "
    "+1} (any of 4 diagonal "
    "directions). The interior "
    "cells along the diagonal are "
    "RESERVED (occupied set "
    "prevents other pairs from "
    "using them). Only the 2 "
    "endpoints are painted. Rule "
    "(FOR EACH COLOR APPEARING "
    "EXACTLY TWICE WHOSE CELLS LIE "
    "ON A 45° DIAGONAL (|DR| = "
    "|DC|), DRAW THE FULL DIAGONAL "
    "LINE BETWEEN THEM IN THAT "
    "COLOR): GROUP cells by color. "
    "For EACH color with exactly 2 "
    "cells: CHECK |dr| == |dc| "
    "(diagonal). PAINT every cell "
    "on the 45° line from "
    "endpoint A to endpoint B "
    "with that color. Net: "
    "endpoint pairs become solid "
    "diagonal colored lines."
)

INVARIANTS = [
    "2-3 colors",
    "each color: 2 cells at (r,c) and (r±k, c±k) for k ≥3",
    "diagonals don't overlap with each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "axis_aligned_pair", "single_endpoint")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "diagonal_pairs",
                       "valid": "diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|axis_aligned_pair|single_endpoint"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 color appearing exactly twice in grid (diagonal pair endpoints)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    from collections import Counter
    flat = [v for row in grid for v in row]
    counts = Counter(v for v in flat if v != 0)
    pairs = [color for color, cnt in counts.items() if cnt == 2]
    if not pairs:
        errs.append("no color appears exactly twice (no diagonal endpoint pairs)")
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
        n_pairs = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_pairs = ctx.draw_int("n_pairs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_pairs)
    occupied = set()
    for color in palette:
        for _ in range(40):
            k = rng.randint(2, 4)
            sr = rng.choice([1, -1])
            sc = rng.choice([1, -1])
            r1 = rng.randint(max(0, -k * sr), min(h - 1, h - 1 - k * sr))
            c1 = rng.randint(max(0, -k * sc), min(w - 1, w - 1 - k * sc))
            r2 = r1 + k * sr
            c2 = c1 + k * sc
            cells = [(r1 + i * sr, c1 + i * sc) for i in range(k + 1)]
            if any(cell in occupied for cell in cells):
                continue
            g[r1][c1] = color
            g[r2][c2] = color
            for cell in cells:
                occupied.add(cell)
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # single cells per color → no pair → no line to draw
        g[2][2] = 4; g[5][7] = 6
        return g
    if name == "axis_aligned_pair":
        # pairs share a row or column (|dr|=0 or |dc|=0) → not diagonal, no line
        g[3][1] = 4; g[3][7] = 4
        g[1][5] = 6; g[6][5] = 6
        return g
    if name == "single_endpoint":
        # only 1 cell per color → can't form a pair, undefined endpoint
        g[2][2] = 4
        g[6][6] = 6
        return g
    return g
