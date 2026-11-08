"""Generator for arc_puzzle_bank_21_set10_s:S10_M7 — Difference highlight across divider.

Rule: find the first column whose every cell is 5 (divider). Output
is the LEFT half (col 0..div-1) where each cell is 8 if it differs
from the corresponding right-half cell (mirrored at div+1+c), else 0.

Combinatorial axes (8): grid_h, half_w, palette_kind, n_left, n_right,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: identical_halves, no_divider, blank_halves.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ca1c02941066"
VERSION = "1.1.1"
TASK_ID = "ca1c02941066"
SUMMARY = "Vertical 5-divider; output highlights cells where left/right halves differ."

INVARIANTS = [
    "exactly one full-column-of-5 divider in the middle",
    "left and right halves have scattered colored cells",
    "≥1 position where halves differ (so output isn't all-zero)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identical_halves", "no_divider", "blank_halves")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "half_w":         {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_left":         {"type": "int", "default": "rng 2..5", "valid": "1..15"},
    "n_right":        {"type": "int", "default": "rng 2..5", "valid": "1..15"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "split_by_divider",
                       "valid": "split_by_divider"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
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
        h = ctx.draw_int("grid_h", 4, 5)
        half_w = ctx.draw_int("half_w", 3, 3)
        n_left = ctx.draw_int("n_left", 2, 3)
        n_right = ctx.draw_int("n_right", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        half_w = ctx.draw_int("half_w", 4, 5)
        n_left = ctx.draw_int("n_left", 4, 5)
        n_right = ctx.draw_int("n_right", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 4, 7)
        half_w = ctx.draw_int("half_w", 3, 5)
        n_left = ctx.draw_int("n_left", 2, 5)
        n_right = ctx.draw_int("n_right", 2, 5)

    w = half_w * 2 + 1
    div = half_w
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][div] = 5

    rng = ctx.draw_rng("scatter")
    color_rng = ctx.draw_rng("colors")

    def place_n(n, c_lo, c_hi):
        positions = [(r, c) for r in range(h) for c in range(c_lo, c_hi + 1)]
        rng.shuffle(positions)
        for r, c in positions[:n]:
            g[r][c] = color_rng.choice([1, 2, 3, 4, 6, 7, 8, 9])

    place_n(n_left, 0, div - 1)
    place_n(n_right, div + 1, w - 1)
    return g


def _draw_from_degenerate(name, rng):
    h, half_w = 5, 3
    w = half_w * 2 + 1
    div = half_w
    g = full_grid(h, w, 0)
    if name == "identical_halves":
        # left and right halves are mirror-identical → diff is empty, output all 0
        for r in range(h):
            g[r][div] = 5
        # left has 4 at (1,1) and 6 at (3,2); mirror at right
        g[1][1] = 4; g[1][div + 1 + (div - 1 - 1)] = 4
        g[3][2] = 6; g[3][div + 1 + (div - 1 - 2)] = 6
        return g
    if name == "no_divider":
        # divider missing → rule fails to identify the split, undefined behavior
        g[1][1] = 4; g[3][2] = 6
        g[2][4] = 8; g[4][5] = 3
        return g
    if name == "blank_halves":
        # divider present but both halves are blank → no diffs to highlight, output all 0
        for r in range(h):
            g[r][div] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid must have a full-column-of-5 divider and >=1 diff between left/right halves."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    # Find the divider column (full column of 5s)
    div = None
    for c in range(w):
        if all(grid[r][c] == 5 for r in range(h)):
            div = c
            break
    if div is None:
        msgs.append("no full-column-of-5 divider found")
        return msgs
    # Check >=1 position where left[r][c] != right[r][reflected_c]
    left_w = div
    right_w = w - div - 1
    diff_found = False
    for r in range(h):
        for lc in range(left_w):
            rc = div + 1 + (left_w - 1 - lc)
            if rc < w:
                if grid[r][lc] != grid[r][rc]:
                    diff_found = True
                    break
        if diff_found:
            break
    if not diff_found:
        msgs.append("no differences between mirrored left/right halves (output would be all-0)")
    return msgs
