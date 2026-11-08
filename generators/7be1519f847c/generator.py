"""Generator for arc_puzzle_bank_eighteenth21:E125.

Fill the center of each monochrome hollow 3x3 ring.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rings,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, filled_centers, mixed_color_ring.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7be1519f847c"
VERSION = "1.1.1"
TASK_ID = "7be1519f847c"

SUMMARY = "Fill the center of each monochrome hollow 3x3 ring."

INVARIANTS = [
    "background is 0",
    "each motif is an isolated 3x3 ring",
    "the eight border cells share one nonzero color",
    "the center cell is initially zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "filled_centers", "mixed_color_ring")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rings":        {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "separated_3x3_rings",
                       "valid": "separated_3x3_rings"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 ring pattern (3×3 nonzero border, zero center)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    rings = 0
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            center = grid[r0 + 1][c0 + 1]
            if center != 0:
                continue
            border = [grid[r0 + dr][c0 + dc]
                      for dr in range(3) for dc in range(3)
                      if not (dr == 1 and dc == 1)]
            if len(set(border)) == 1 and border[0] != 0:
                rings += 1
    if rings < 1:
        return ["expected ≥1 3×3 ring (nonzero border, zero center); found none"]
    return []


def _free(g, r0, c0):
    h, w = len(g), len(g[0])
    for r in range(max(0, r0 - 1), min(h, r0 + 4)):
        for c in range(max(0, c0 - 1), min(w, c0 + 4)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("n_rings", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_rings", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("n_rings", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(180):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 3)
        c0 = rng.randint(0, w - 3)
        if not _free(g, r0, c0):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for dr in range(3):
            for dc in range(3):
                if not (dr == 1 and dc == 1):
                    g[r0 + dr][c0 + dc] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # blank → no ring centers to fill
        return g
    if name == "filled_centers":
        # ring centers already non-zero → "center is zero" precondition fails
        for dr in range(3):
            for dc in range(3):
                g[1 + dr][1 + dc] = 4
        return g
    if name == "mixed_color_ring":
        # 8 border cells use 2 colors → "share one nonzero color" precondition fails
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)]:
            g[1 + dr][1 + dc] = 4
        for dr, dc in [(2, 0), (2, 1), (2, 2)]:
            g[1 + dr][1 + dc] = 6
        return g
    return g
