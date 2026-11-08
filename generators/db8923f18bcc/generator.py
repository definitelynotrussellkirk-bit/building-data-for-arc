"""Generator for arc_puzzle_bank_21_set9_e:easy_i03.

Complete each monochrome L-triomino into a 2x2 square.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blocks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, full_2x2, two_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db8923f18bcc"
VERSION = "2.0.0"
TASK_ID = "db8923f18bcc"

SUMMARY = (
    "0-bg grid (h~6-8, w~6-8) with 2-4 ISOLATED L-TRIOMINOES — "
    "each is a 2×2 window with EXACTLY 3 of the 4 cells painted "
    "in ONE non-0 color from {1..9}; the FOURTH (missing) "
    "CORNER is 0. Which of the 4 corners is missing is random "
    "per triomino. Triominoes are placed at non-touching "
    "positions with 1-cell 8-conn padding (so each L-shape sits "
    "alone in its 2×2 window, no shared cells between any two). "
    "If random placement fails entirely, generator emits a "
    "single fallback L at (1,1)-(2,1). Rule (FILL MISSING "
    "CORNER OF EACH MONOCHROME L INTO A 2×2 SQUARE): For EACH "
    "2×2 WINDOW where exactly 3 cells share ONE non-0 color C "
    "and the fourth cell is 0: RECOLOR the missing-corner 0 "
    "cell to C, completing the 2×2 monochrome square. Other "
    "cells (already filled with C, or outside any active 2×2 "
    "window) stay unchanged. Net: every L-triomino is closed "
    "into a solid 2×2 monochrome block of its own color."
)

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has three cells of one nonzero color",
    "active windows are isolated",
    "the missing 2x2 corner is black before completion",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "full_2x2", "two_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blocks":       {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_l_triominoes",
                       "valid": "isolated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 6, 7)
        target = ctx.draw_int("blocks", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("blocks", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 6, 8)
        target = ctx.draw_int("blocks", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(160):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        if not _free(g, r0, c0):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        missing = rng.randrange(4)
        cells = [(r0, c0), (r0, c0 + 1), (r0 + 1, c0), (r0 + 1, c0 + 1)]
        for idx, (r, c) in enumerate(cells):
            if idx != missing:
                g[r][c] = color
        placed += 1
    if placed == 0:
        g[1][1] = g[1][2] = g[2][1] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # blank → no L-triominoes to complete
        return g
    if name == "full_2x2":
        # 2x2 already complete → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 4
        return g
    if name == "two_corners":
        # only 2 corners → "exactly three" precondition fails
        g[1][1] = 4; g[2][2] = 4
        return g
    return g
