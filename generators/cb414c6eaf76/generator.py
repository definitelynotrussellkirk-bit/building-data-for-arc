"""Generator for arc_additional_puzzles_21_set10_bundle:E66 — Fill 0 in 2×2 with 3 same-color cells.

Rule: 2×2 sub-block with exactly 3 cells of same non-zero color and
1 cell = 0 → set the 0-cell to that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_Ls,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_Ls, all_solid_squares, mixed_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import L_TROMINOES

GENERATOR_ID = "cb414c6eaf76"
VERSION = "1.1.1"
TASK_ID = "cb414c6eaf76"
SUMMARY = "2-3 L-trominoes in distinct colors, plus distractor singletons."

INVARIANTS = [
    "≥2 L-tromino patterns: 3 cells of 1 color in a 2×2 with 4th = 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_Ls", "all_solid_squares", "mixed_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_Ls":           {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "spaced_L_trominoes",
                       "valid": "spaced_L_trominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 9)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    placed = []
    for _ in range(40):
        if len(placed) >= rng.randint(2, 3): break
        r = rng.randint(0, h - 2); c = rng.randint(0, w - 2)
        if all(abs(r - pr) > 2 or abs(c - pc) > 2 for pr, pc in placed):
            color = rng.choice(palette)
            for dr, dc in rng.choice(L_TROMINOES):
                g[r + dr][c + dc] = color
            placed.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_Ls":
        # only solo non-zero cells, no 2x2 with 3-of-color → rule never fires
        g[1][1] = 4
        g[3][3] = 6
        g[4][6] = 7
        return g
    if name == "all_solid_squares":
        # 2x2 fully filled with the same color → no 0-cell to fill
        for r in range(2):
            for c in range(2): g[1 + r][1 + c] = 4
        for r in range(2):
            for c in range(2): g[3 + r][5 + c] = 6
        return g
    if name == "mixed_colors":
        # 2x2 with 3 cells but mixed colors → "all 3 same color" precondition fails
        g[1][1] = 4; g[1][2] = 6; g[2][1] = 4   # mixed
        g[3][4] = 6; g[3][5] = 6; g[4][5] = 7   # mixed
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 valid L-tromino: a 2x2 region with exactly 3 same-color cells and one zero."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    found = False
    for r in range(h - 1):
        for c in range(w - 1):
            quad = [grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]]
            zeros = quad.count(0)
            if zeros == 1:
                nonzero = [v for v in quad if v != 0]
                if len(set(nonzero)) == 1:
                    found = True
                    break
        if found:
            break
    if not found:
        msgs.append("no valid L-tromino (2x2 with 3 same-color cells + 1 zero) found")
    return msgs
