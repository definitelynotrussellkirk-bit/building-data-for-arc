"""Generator for arc_puzzle_bank_21_set8_s:S8_E5.

Rule: each horizontal run keeps alternating cells starting from its left
endpoint; even-indexed cells (within run) are kept, odd erased.

Combinatorial axes (8): grid_h, grid_w, palette_kind, run_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_runs, runs_too_short, runs_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f5bd0601f95"
VERSION = "1.1.1"
TASK_ID = "4f5bd0601f95"
SUMMARY = "Each horizontal run keeps alternating cells starting from its left endpoint."

INVARIANTS = [
    "background is 0",
    "there are several horizontal runs of length at least three",
    "outputs keep run cells with even local index",
    "all other run cells are erased",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_runs", "runs_too_short", "runs_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "run_count":      {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "row_separated",
                       "valid": "row_separated"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _fill_run(g, r, c0, length, color):
    for c in range(c0, c0 + length):
        g[r][c] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 horizontal run of length >=3 (all cells same non-zero color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    found_run = False
    for r in range(h):
        c = 0
        while c < w:
            if grid[r][c] != 0:
                start = c
                color = grid[r][c]
                while c < w and grid[r][c] == color:
                    c += 1
                if c - start >= 3:
                    found_run = True
                    break
            else:
                c += 1
        if found_run:
            break
    if not found_run:
        errs.append("no horizontal run of length >=3 found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 9, 10)
        count = min(ctx.draw_int("run_count", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 11, 13)
        count = min(ctx.draw_int("run_count", 4, 5), h)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 9, 13)
        count = min(ctx.draw_int("run_count", 2, 5), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), count)
    colors = [2, 3, 4, 6, 7]
    for idx, r in enumerate(rows):
        length = rng.randint(3, min(6, w))
        c0 = rng.randint(0, w - length)
        _fill_run(g, r, c0, length, colors[idx % len(colors)])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_runs":
        # empty grid → nothing to keep-alternate
        return g
    if name == "runs_too_short":
        # length-1 or length-2 runs only → alternation is trivial (keep first cell only)
        g[1][2] = 4
        g[3][5] = 6; g[3][6] = 6
        g[5][1] = 7
        return g
    if name == "runs_overlap":
        # two runs of different colors share a row → boundary ambiguity
        g[2][1] = 4; g[2][2] = 4; g[2][3] = 4
        g[2][4] = 6; g[2][5] = 6; g[2][6] = 6
        return g
    return g
