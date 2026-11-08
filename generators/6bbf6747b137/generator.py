"""Generator for arc_puzzle_bank_seventh21:M43 — header-count area select.

Rule: count of 1s in row 0 = K. Keep below-row-0 blobs whose size = K.

Combinatorial axes (8): grid_h, grid_w, palette_kind, K,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_matching_blob, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "6bbf6747b137"
VERSION = "1.2.0"
TASK_ID = "6bbf6747b137"
SUMMARY = "Row 0 has K 1-cells (K=1..6) + 3 blobs below at distinct sizes, exactly one of size K."

INVARIANTS = [
    "background is 0",
    "row 0 has K 1-markers (K ∈ 1..6)",
    "3 below-row-0 blobs at strictly distinct sizes; exactly one has size K",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_matching_blob", "all_same_size")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "K":              {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "row0_count_with_below_blobs",
                       "valid": "row0_count_with_below_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the basic header/body domain, including valid K=1 draws."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    row0_ones = [c for c in range(w) if grid[0][c] == 1]
    if not row0_ones:
        return errs  # degenerate (no_markers) — allowed
    if len(row0_ones) > 6:
        errs.append(f"row 0 has {len(row0_ones)} color-1 markers; K should be <=6")
    body = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if not body:
        errs.append("row 0 has markers but no body blobs")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    K = ctx.draw_int_strict("K", 1, 6)
    cols = rng.sample(range(w), K)
    for c in cols:
        g[0][c] = 1
    used = {(0, c) for c in cols}
    for c in range(w):
        used.add((1, c))
    other_sizes = rng.sample([s for s in range(1, 7) if s != K], 2)
    sizes = [K] + other_sizes
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # row 0 blank → K=0, no blobs match, output blank
        for (r, c) in [(3, 1), (3, 2), (4, 1)]: g[r][c] = 4  # size 3
        for (r, c) in [(6, 5), (6, 6)]: g[r][c] = 6  # size 2
        return g
    if name == "no_matching_blob":
        # K=2 but no blob has size 2 → rule fires zero times, output blank
        g[0][1] = 1; g[0][3] = 1
        for (r, c) in [(3, 1), (3, 2), (4, 1)]: g[r][c] = 4  # size 3
        for (r, c) in [(6, 5), (6, 6), (6, 7), (7, 6)]: g[r][c] = 6  # size 4
        return g
    if name == "all_same_size":
        # all blobs same size → K matches all of them simultaneously
        g[0][1] = 1; g[0][3] = 1; g[0][5] = 1  # K=3
        for (r, c) in [(3, 1), (3, 2), (4, 1)]: g[r][c] = 4  # size 3
        for (r, c) in [(6, 5), (6, 6), (7, 6)]: g[r][c] = 6  # size 3
        return g
    return g
