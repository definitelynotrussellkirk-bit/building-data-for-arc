"""Generator for arc_puzzle_bank_fifth21:E31.

Place isolated diagonal pairs inside 2x2 windows to complete squares.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, full_2x2, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b4d9320e0d9d"
VERSION = "2.1.0"  # pair colors are now sampled without replacement
TASK_ID = "b4d9320e0d9d"

SUMMARY = (
    "0-bg grid (h×w, h=7..9, w=7..10) with 2-4 isolated 'diagonal "
    "pair' 2×2 windows. Each pair has two SAME-COLOR cells on ONE "
    "diagonal of a 2×2 window (main: (r,c)+(r+1,c+1) or anti: "
    "(r,c+1)+(r+1,c)) and 0 on the other two corners. Pairs use "
    "DISTINCT colors from 1-9. Pairs are isolated (≥1-cell buffer). "
    "Rule: scan every 2×2 window. If a same-color non-zero pair sits "
    "on the main diagonal with the anti-diagonal both 0, set the "
    "anti-diagonal cells to the same color (completing the 2×2 "
    "square). Symmetrically, if pair is on anti-diagonal with main "
    "both 0, set main cells to that color. Otherwise window stays."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-4 isolated 2x2 diagonal pairs, each in a distinct non-zero color",
    "for each pair: 2 same-color cells on one diagonal, 0 on the other",
    "pairs are isolated (≥1-cell buffer) so completions don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "full_2x2", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "isolated_diag_pairs",
                       "valid": "isolated_diag_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r0, c0):
    h, w = len(g), len(g[0])
    for r in range(max(0, r0 - 1), min(h, r0 + 3)):
        for c in range(max(0, c0 - 1), min(w, c0 + 3)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
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
    placed = 0
    pair_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], target)
    for _ in range(260):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        if not _free(g, r0, c0):
            continue
        color = pair_colors[placed]
        if rng.randrange(2):
            cells = [(r0, c0), (r0 + 1, c0 + 1)]
        else:
            cells = [(r0, c0 + 1), (r0 + 1, c0)]
        for r, c in cells:
            g[r][c] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal pairs to complete into squares
        return g
    if name == "full_2x2":
        # 2x2 already filled → no orthogonal corners to add
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 4
        return g
    if name == "single_cell":
        # single cells → not pairs, no diagonal to complete
        g[2][2] = 4
        g[5][5] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    wins = []
    for r in range(h - 1):
        for c in range(w - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                wins.append((r, c, a, "main"))
            if b != 0 and b == d and a == 0 and e == 0:
                wins.append((r, c, b, "anti"))
    if not (2 <= len(wins) <= 4):
        errors.append(f"expected 2..4 isolated diagonal-pair windows, got {len(wins)}")
    colors = [x[2] for x in wins]
    if len(set(colors)) != len(colors):
        errors.append(f"diagonal-pair colors are not distinct: {colors}")
    return errors
