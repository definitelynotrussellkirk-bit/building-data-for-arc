"""Generator for easy_k06: keep only the main diagonal of solid 2x2 blocks.

Rule: each solid 2×2 block → keep only its (top-left, bottom-right)
diagonal cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blocks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, blocks_overlap, single_cell_blocks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56cfec365918"
VERSION = "1.1.1"
TASK_ID = "56cfec365918"
SUMMARY = "Separated solid 2x2 color blocks reduce to their top-left/bottom-right diagonal."
INVARIANTS = [
    "each generated object is a solid monochrome 2x2 block",
    "2x2 blocks are separated by background",
    "background is zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "blocks_overlap", "single_cell_blocks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blocks":       {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "grid_aligned_3_step",
                       "valid": "grid_aligned_3_step"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
        n = ctx.draw_int("n_blocks", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n_blocks", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 6, 10)
        n = ctx.draw_int("n_blocks", 2, 5)
    rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("colors", n=min(n, 9), exclude={0}))
    g = full_grid(h, w, 0)
    spots = [(r, c) for r in range(0, h - 1, 3) for c in range(0, w - 1, 3)]
    rng.shuffle(spots)
    for i, (r, c) in enumerate(spots[:n]):
        color = colors[i % len(colors)]
        g[r][c] = color
        g[r + 1][c] = color
        g[r][c + 1] = color
        g[r + 1][c + 1] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one solid 2x2 block (all 4 cells same non-zero color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    found = False
    for r in range(h - 1):
        for c in range(w - 1):
            v = grid[r][c]
            if v != 0 and grid[r + 1][c] == v and grid[r][c + 1] == v and grid[r + 1][c + 1] == v:
                found = True
    if not found:
        errs.append("no solid 2x2 block found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # empty grid → no 2x2 blocks to reduce
        return g
    if name == "blocks_overlap":
        # 2x2 blocks share cells → diagonal extraction would be entangled
        for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]: g[r][c] = 4
        for r, c in [(2, 2), (2, 3), (3, 2), (3, 3)]: g[r][c] = 6
        return g
    if name == "single_cell_blocks":
        # just isolated cells, not 2x2 blocks → diagonal not well-defined
        g[1][1] = 4
        g[4][4] = 6
        g[6][2] = 7
        return g
    return g
