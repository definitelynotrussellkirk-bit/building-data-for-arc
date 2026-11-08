"""Generator for arc_puzzle_bank_21_set22_bundle:easy_p03.

Combinatorial axes (8): grid_h, grid_w, palette_kind, block_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, complete_2x2, two_holes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9296fec26a94"
VERSION = "1.2.1"  # add self_check
TASK_ID = "9296fec26a94"
SUMMARY = "Separated 2x2 windows each contain exactly 3 same-color cells and 1 blank (zero) corner. Rule fills the blank corner of each such window with that window's color, completing it into a solid 2x2."

# Rivals: 'output is input' refuted by any demo (blanks fill).
# 'fill all bg cells' refuted by any demo where lone 0 cells stay.
# 'use bg/random color for fill' refuted by any demo (fill matches
# block color). 'fill 4-cell-complete blocks' refuted by demos where
# 2-cell or 4-cell groups don't get touched. 3 demos cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has exactly one zero",
    "active windows do not overlap or touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "complete_2x2", "two_holes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "block_count":    {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "incomplete_2x2_one_hole",
                       "valid": "incomplete_2x2_one_hole"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 2×2 window with exactly 3 same-color non-zero cells and 1 zero."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    windows = []
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [grid[r][c], grid[r][c+1], grid[r+1][c], grid[r+1][c+1]]
            nz = [v for v in vals if v != 0]
            if len(nz) == 3 and len(set(nz)) == 1:
                windows.append((r, c))
    if not windows:
        return ["expected ≥1 2×2 block with 3 same-color cells and 1 zero; found none"]
    return []


def _clear_neighborhood(grid, r0, c0):
    h = len(grid)
    w = len(grid[0])
    for r in range(max(0, r0 - 1), min(h, r0 + 3)):
        for c in range(max(0, c0 - 1), min(w, c0 + 3)):
            if grid[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        block_count = ctx.draw_int("block_count", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        block_count = ctx.draw_int("block_count", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        block_count = ctx.draw_int("block_count", 3, 5)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    positions = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    rng.shuffle(positions)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], block_count)
    placed = 0
    for r0, c0 in positions:
        if placed >= block_count:
            break
        if not _clear_neighborhood(grid, r0, c0):
            continue
        missing = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
        color = colors[placed]
        for dr in range(2):
            for dc in range(2):
                if (dr, dc) != missing:
                    grid[r0 + dr][c0 + dc] = color
        placed += 1
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # blank → no incomplete blocks to complete
        return g
    if name == "complete_2x2":
        # 2x2 already complete → no missing corner to fill
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
                g[5 + dr][6 + dc] = 6
        return g
    if name == "two_holes":
        # only 2 cells of a 2x2 (2 holes) → ambiguous which corner to complete
        g[1][1] = 4; g[2][2] = 4
        g[5][6] = 6; g[6][7] = 6
        return g
    return g
