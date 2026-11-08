"""Generator for arc_puzzle_bank_21_set16_s:S16_M4 — span between pair points (per-color).

Rule: each color appearing exactly twice draws a Bresenham line span
between the two cells, painted in its OWN color (vs S16_M2 which uses 8).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_cell_colors, three_cell_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "68fd8016de39"
VERSION = "2.0.1"  # self_check + fail closed if a pair cannot be placed
TASK_ID = "68fd8016de39"
SUMMARY = (
    "0-bg grid (h, w ~8-11) with 2-3 color PAIRS — each "
    "pair = two cells of the same color at random "
    "positions with Manhattan distance ≥3. Pairs may be "
    "horizontal, vertical, or diagonal/skew. Different "
    "pairs use distinct colors. Rule: for each color "
    "appearing exactly twice, draw a BRESENHAM-style "
    "LINE SPAN between the two endpoints, painting "
    "every intermediate cell along the line with the "
    "SAME color. Endpoints stay. Net: each pair "
    "becomes a continuous straight or staircase line."
)

INVARIANTS = [
    "background is 0",
    "every non-zero color appears exactly twice",
    "pairs may align horizontal, vertical, or diagonal (Bresenham span)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_cell_colors", "three_cell_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..13"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "pair_endpoints",
                       "valid": "pair_endpoints"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_pairs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n = ctx.draw_int("n_pairs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)
    for color in palette:
        placed = False
        for _ in range(40):
            r1 = rng.randint(0, h - 1)
            c1 = rng.randint(0, w - 1)
            r2 = rng.randint(0, h - 1)
            c2 = rng.randint(0, w - 1)
            if abs(r1 - r2) + abs(c1 - c2) < 3:
                continue
            if g[r1][c1] != 0 or g[r2][c2] != 0:
                continue
            g[r1][c1] = color
            g[r2][c2] = color
            placed = True
            break
        if not placed:
            raise ValueError("could not place a distance>=3 color pair")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no pairs to span
        return g
    if name == "single_cell_colors":
        # only singletons, no color appears twice → "exactly twice" precondition fails
        g[1][1] = 4
        g[3][5] = 6
        g[7][7] = 7
        return g
    if name == "three_cell_colors":
        # color appears 3 times → "exactly twice" precondition fails
        g[1][1] = 4; g[5][5] = 4; g[7][2] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    pos = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                pos.setdefault(v, []).append((r, c))
    if len(pos) < 2:
        errs.append(f"expected at least 2 color pairs, got {len(pos)}")
    for color, cells in sorted(pos.items()):
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times, expected exactly 2")
            continue
        (r1, c1), (r2, c2) = cells
        if abs(r1 - r2) + abs(c1 - c2) < 3:
            errs.append(f"color {color} pair endpoints are too close")
    return errs
