"""Generator for arc_puzzle_bank_21_set9_s:S9_M7 — connect aligned pairs.

Rule: each color appearing exactly twice draws a horizontal or vertical
line connecting the two cells in that color (only if same row or same
col).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, all_adjacent, diagonal_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "97dd5f3c96b9"
VERSION = "1.1.1"
TASK_ID = "97dd5f3c96b9"
SUMMARY = "2-3 colors each twice on the grid, each pair sharing a row or col."

INVARIANTS = [
    "background is 0",
    "each non-zero color appears exactly twice",
    "each pair shares a row OR a column (but not both)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "all_adjacent", "diagonal_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "axis_aligned_pairs",
                       "valid": "axis_aligned_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: each non-bg color appears exactly twice; each pair shares row OR col."""
    if not grid or not grid[0]:
        return ["empty grid"]
    from collections import defaultdict
    pos: dict = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                pos[v].append((r, c))
    if not pos:
        return []  # degenerate — allowed
    errs = []
    for color, cells in pos.items():
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times; expected 2")
            continue
        (r0, c0), (r1, c1) = cells
        if r0 != r1 and c0 != c1:
            errs.append(f"color {color} pair at ({r0},{c0}) and ({r1},{c1}) shares neither row nor col")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_pairs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_pairs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for color in palette:
        for _ in range(40):
            if rng.random() < 0.5:
                r = rng.randint(0, h - 1)
                c1 = rng.randint(0, w - 4)
                c2 = rng.randint(c1 + 3, w - 1)
                if g[r][c1] == 0 and g[r][c2] == 0:
                    g[r][c1] = color
                    g[r][c2] = color
                    break
            else:
                c = rng.randint(0, w - 1)
                r1 = rng.randint(0, h - 4)
                r2 = rng.randint(r1 + 3, h - 1)
                if g[r1][c] == 0 and g[r2][c] == 0:
                    g[r1][c] = color
                    g[r2][c] = color
                    break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # only single cells, no pair → no line drawn
        g[2][2] = 4; g[5][7] = 6
        return g
    if name == "all_adjacent":
        # pairs are adjacent (gap < 3) → degenerate "line" of length 0
        g[2][2] = 4; g[2][3] = 4
        g[5][6] = 6; g[6][6] = 6
        return g
    if name == "diagonal_pair":
        # pairs share neither row nor col → no line possible
        g[1][1] = 4; g[5][7] = 4
        g[2][6] = 6; g[6][2] = 6
        return g
    return g
