"""Generator for arc_puzzle_bank_next21:E12.

Rule: place exact horizontal dominoes with a zero cell to their right.

Combinatorial axes (8): grid_h, grid_w, palette_kind, dominoes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dominoes, length_3_run, dominoes_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c5a96370d612"
VERSION = "1.1.1"
TASK_ID = "c5a96370d612"
SUMMARY = "Place exact horizontal dominoes with a zero cell to their right."

INVARIANTS = [
    "background is 0",
    "each target run is horizontal and length exactly 2",
    "the cell immediately right of each domino is initially 0",
    "rows are separated or contain only one domino to avoid merging",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dominoes", "length_3_run", "dominoes_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..14"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "dominoes":       {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_separated",
                       "valid": "row_separated"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
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
        w = ctx.draw_int("grid_w", 7, 9)
        target = min(ctx.draw_int("dominoes", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
        target = min(ctx.draw_int("dominoes", 3, 4), h)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 7, 11)
        target = min(ctx.draw_int("dominoes", 2, 4), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), target)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(target, 9))
    for i, r in enumerate(rows):
        c0 = rng.randint(0, w - 3)
        color = colors[i % len(colors)]
        g[r][c0] = color
        g[r][c0 + 1] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 horizontal domino (two adjacent same-color cells in a row)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    dominoes = [(r, c) for r in range(h) for c in range(w - 1)
                if grid[r][c] != 0 and grid[r][c] == grid[r][c + 1]]
    if not dominoes:
        errors.append("no horizontal dominoes (adjacent same-color cells) found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_dominoes":
        # empty grid — nothing to place
        return g
    if name == "length_3_run":
        # length-3 same-color run → predicate "exactly 2" fails
        for dc in range(3):
            g[2][2 + dc] = 4
        return g
    if name == "dominoes_touching":
        # two dominoes share an edge (no zero gap) → "right cell empty" invariant fails
        g[2][1] = 4; g[2][2] = 4
        g[2][3] = 6; g[2][4] = 6
        return g
    return g
