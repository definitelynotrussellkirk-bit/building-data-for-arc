"""Generator for arc_puzzle_bank_21_set8:easy_h05.

Rule: rewrite each filled monochrome 2x2 block to its anti-diagonal.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blocks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, partial_blocks, blocks_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8fbc7756d37f"
VERSION = "1.1.1"  # self_check
TASK_ID = "8fbc7756d37f"
SUMMARY = "Rewrite each filled monochrome 2x2 block to its anti-diagonal."

INVARIANTS = [
    "background is 0",
    "objects are isolated filled 2x2 blocks",
    "each block is monochrome",
    "output keeps only top-right and bottom-left cells of each block",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "partial_blocks", "blocks_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "blocks":         {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_2x2_blocks",
                       "valid": "spaced_2x2_blocks"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blocks|partial_blocks|blocks_overlap"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("blocks", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
        target = ctx.draw_int("blocks", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 11)
        target = ctx.draw_int("blocks", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(180):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        if not _free(g, r0, c0):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r in (r0, r0 + 1):
            for c in (c0, c0 + 1):
                g[r][c] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # blank grid → no 2x2 blocks, rule fires zero times
        return g
    if name == "partial_blocks":
        # L-shapes (3 cells) instead of 2x2 → predicate "filled 2x2" fails, rule does nothing
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for (r, c) in [(4, 5), (5, 5), (5, 6)]: g[r][c] = 6
        return g
    if name == "blocks_overlap":
        # adjacent blocks share cells → ambiguous which block they belong to; predicate fails
        for r in range(1, 3):
            for c in range(1, 3): g[r][c] = 4
        for r in range(2, 4):   # overlaps row 2 with above
            for c in range(2, 4): g[r][c] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    h, w = len(grid), len(grid[0])
    blocks = []
    covered = set()
    for r in range(h - 1):
        for c in range(w - 1):
            vals = {grid[r][c], grid[r + 1][c], grid[r][c + 1], grid[r + 1][c + 1]}
            if len(vals) == 1 and 0 not in vals:
                block = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
                blocks.append((r, c))
                covered |= block
    nonzero = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(blocks) < 2:
        errs.append(f"expected at least two filled 2x2 blocks, got {len(blocks)}")
    if covered != nonzero:
        errs.append("nonzero cells are not exactly covered by isolated filled 2x2 blocks")
    return errs
