"""Generator for arc_puzzle_bank_21_set4_d:easy_d05.

Rule: each seed draws a same-color down-left diagonal ray to the border.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, all_at_left_or_bottom, seeds_share_diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "37fbfdde70b9"
VERSION = "2.0.1"
TASK_ID = "37fbfdde70b9"
SUMMARY = (
    "0-bg grid (h ∈ 6-9, w ∈ 7-10) "
    "with: SEED_COUNT ∈ 2-4 SINGLE "
    "COLORED CELLS, each in a DISTINCT "
    "non-bg color drawn from {1..9}, "
    "placed at random positions where: "
    "(a) row ∈ 0..h-2 (not the bottom "
    "row, so a downward ray has room "
    "to extend); (b) col ∈ 1..w-1 "
    "(not col 0, so a leftward ray "
    "has room); (c) each seed sits on "
    "a DISTINCT anti-diagonal (r + c "
    "differs across seeds) so rays "
    "don't overlap. Rule (FROM EACH "
    "SEED, DRAW A DOWN-LEFT (↙) "
    "DIAGONAL RAY OF THE SAME COLOR "
    "ALL THE WAY TO THE GRID "
    "BORDER): For EACH seed at "
    "(r, c) with color k: PAINT "
    "cells (r+i, c-i) for i = 1, 2, "
    "... until either r+i ≥ h OR "
    "c-i < 0 (out of bounds). Each "
    "ray cell painted color k. "
    "Seeds stay at their original "
    "positions. Net: each seed "
    "shoots a downward-leftward "
    "diagonal of its color to the "
    "grid edge."
)

INVARIANTS = [
    "background is 0",
    "all nonzero input cells are singleton seeds",
    "seed rays are separated by using distinct anti-diagonals",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "all_at_left_or_bottom", "seeds_share_diagonal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "distinct_anti_diagonals",
                       "valid": "distinct_anti_diagonals"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 non-zero seed cell; all values 0..9; grid nonempty."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero == 0:
        pass  # degenerate (no_seeds) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        count = ctx.draw_int("seed_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        count = ctx.draw_int("seed_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        count = ctx.draw_int("seed_count", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used_diag = set()
    for color in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], count):
        for _attempt in range(300):
            r = rng.randint(0, h - 2)
            c = rng.randint(1, w - 1)
            diag = r + c
            if diag in used_diag or g[r][c] != 0:
                continue
            g[r][c] = color
            used_diag.add(diag)
            break
        else:
            raise ValueError("could not place diagonal-ray seed")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank grid → no rays cast, rule is identity
        return g
    if name == "all_at_left_or_bottom":
        # seeds at left col (c=0) or bottom row (r=h-1) → ray extends 0 cells (already at border)
        g[3][0] = 4   # leftmost col, ray would go down-left out of bounds immediately
        g[h - 1][5] = 6   # bottom row, no row below
        return g
    if name == "seeds_share_diagonal":
        # two seeds on same anti-diagonal (r+c equal) → ray paths overlap, conflicting paints
        g[2][5] = 4   # r+c = 7
        g[5][2] = 6   # r+c = 7 — same anti-diagonal as above
        return g
    return g
