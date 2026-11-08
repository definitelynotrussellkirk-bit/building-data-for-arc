"""Generator for arc_puzzle_bank_21_set19_bundle:easy_p07.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rectangle_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_corners, complete_rect, two_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "702934c31043"
VERSION = "1.2.1"
TASK_ID = "702934c31043"
SUMMARY = "Per color: 3 of the 4 axis-aligned-rectangle corners are present (one is blank). Rule completes each such 3-of-4 rectangle by filling the missing corner with the same color. Multiple rectangles in different colors are independent."

# Rivals: 'output is input' refuted by any demo (missing corner
# fills). 'fill all 4 corners regardless' refuted by ≥1 demo where
# a 2-corner pair without a third does NOT fill. 'use color from
# another color' refuted by any multi-color demo (each color
# completes its own rect). 'fill arbitrary cell, not corner'
# refuted by any demo (only corners change). 3 demos with ≥2
# distinct colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each color appears in exactly three corners of one rectangle",
    "rectangles use distinct colors and do not share corner cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corners", "complete_rect", "two_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rectangle_count":{"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "three_of_four_corners",
                       "valid": "three_of_four_corners"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 distinct non-zero color each with exactly 3 cells; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        errs.append("no non-zero cells found")
        return errs
    bad = [c for c, n in counts.items() if n != 3]
    if bad:
        errs.append(f"colors with count != 3 (expected 3-of-4 corners): {bad}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng_size = ctx.draw_rng("size")
    if difficulty == "easy":
        h = rng_size.randint(6, 9); w = rng_size.randint(8, 11)
        rectangle_count = rng_size.randint(1, 2)
    elif difficulty == "hard":
        h = rng_size.randint(12, 16); w = rng_size.randint(14, 18)
        rectangle_count = rng_size.randint(3, 5)
    else:
        h = rng_size.randint(8, 11); w = rng_size.randint(10, 14)
        rectangle_count = rng_size.randint(2, 4)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], rectangle_count)
    attempts = 0
    placed = 0
    while placed < rectangle_count and attempts < 200:
        attempts += 1
        r1, r2 = sorted(rng.sample(range(h), 2))
        c1, c2 = sorted(rng.sample(range(w), 2))
        if r1 == r2 or c1 == c2:
            continue
        corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
        if any(corner in used for corner in corners):
            continue
        missing = rng.choice(corners)
        color = colors[placed]
        for corner in corners:
            if corner == missing:
                continue
            r, c = corner
            grid[r][c] = color
            used.add(corner)
        used.add(missing)
        placed += 1
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_corners":
        # blank → no rectangle corners to complete
        return g
    if name == "complete_rect":
        # all 4 corners present → no missing corner to fill, identity
        for r, c in [(1, 1), (1, 6), (5, 1), (5, 6)]: g[r][c] = 4
        return g
    if name == "two_corners":
        # only 2 corners present → can't infer the rectangle uniquely
        g[1][1] = 4; g[5][6] = 4
        return g
    return g
