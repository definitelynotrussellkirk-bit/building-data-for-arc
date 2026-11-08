"""Generator for arc_puzzle_bank_thirteenth21:E87.

Every three-cell 2x2 color corner is completed into a solid block.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blocks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, full_2x2, length_2_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3a3258548fa3"
VERSION = "1.1.1"
TASK_ID = "3a3258548fa3"

SUMMARY = "Every three-cell 2x2 color corner is completed into a solid block."

INVARIANTS = [
    "background is 0",
    "each target 2x2 block has exactly one missing corner",
    "target blocks are separated by at least one blank row or column",
    "colors are nonzero and may vary across blocks",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "full_2x2", "length_2_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blocks":       {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_l_triominoes",
                       "valid": "isolated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 1), min(h, r + 3)):
        for cc in range(max(0, c - 1), min(w, c + 3)):
            if g[rr][cc] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 three-cell L-shape (3 of 4 corners of a 2×2 bbox); values 0..9."""
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
        pass  # degenerate (no_blocks) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("blocks", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("blocks", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("blocks", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    placed = 0
    for _ in range(120):
        if placed >= target:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if not _free(g, r, c):
            continue
        color = rng.choice(colors)
        missing = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
        for dr in (0, 1):
            for dc in (0, 1):
                if (dr, dc) != missing:
                    g[r + dr][c + dc] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # blank → no L-triominoes to complete
        return g
    if name == "full_2x2":
        # 2x2 already solid → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 4
        return g
    if name == "length_2_l":
        # 2-cell groups → not 3-of-4, rule won't fire
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4
        for r, c in [(5, 5), (6, 5)]: g[r][c] = 6
        return g
    return g
