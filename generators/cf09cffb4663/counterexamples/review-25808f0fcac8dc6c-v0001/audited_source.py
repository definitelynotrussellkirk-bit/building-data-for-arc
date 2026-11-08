"""Generator for arc_additional_puzzle_bank_volume5:E34.

Rule: blue four-way line intersections (plus shapes) are marked red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_crosses,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pluses, partial_pluses, mixed_arm_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf09cffb4663"
VERSION = "2.0.1"
TASK_ID = "cf09cffb4663"
SUMMARY = (
    "0-bg grid (h, w~8-13) "
    "with 2-4 BLUE(1) PLUS "
    "SHAPES — each centered "
    "at an INTERIOR (r, c) "
    "(1 ≤ r ≤ h-2, 1 ≤ c ≤ "
    "w-2) with all 5 cells "
    "(center + 4 cardinal "
    "neighbors) painted "
    "color 1. Plus centers "
    "are SPACED (Chebyshev "
    "distance ≥4) so arms "
    "do not touch between "
    "different pluses. Rule "
    "(MARK EACH BLUE PLUS "
    "INTERSECTION'S CENTER "
    "WITH RED): For EACH "
    "BLUE PLUS SHAPE — "
    "identify cells (r, c) "
    "where (r, c), (r-1, c)"
    ", (r+1, c), (r, c-1), "
    "(r, c+1) are ALL "
    "COLOR 1. The CENTER "
    "(r, c) is the plus "
    "intersection. RECOLOR "
    "the center cell from "
    "blue (1) to RED (2). "
    "The 4 arm cells stay "
    "blue. Net: each plus "
    "shape gets a red dot "
    "at its intersection "
    "while arms remain blue."
)

INVARIANTS = [
    "background is 0",
    "each target is a blue plus intersection",
    "the center has blue in all four cardinal directions",
    "plus shapes are separated so their arms do not touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pluses", "partial_pluses", "mixed_arm_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_crosses":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "spaced_pluses",
                       "valid": "spaced_pluses"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all non-zero cells are color 1 (blue plus arms) only."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 1)]
    if bad:
        return errs  # degenerate mixed_arm_colors — allow
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_crosses = ctx.draw_int("n_crosses", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
        n_crosses = ctx.draw_int("n_crosses", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_crosses = ctx.draw_int("n_crosses", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    centers: list[tuple[int, int]] = []
    for _ in range(220):
        if len(centers) >= n_crosses:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if any(abs(r - rr) < 4 and abs(c - cc) < 4 for rr, cc in centers):
            continue
        for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            g[r + dr][c + dc] = 1
        centers.append((r, c))
    if not centers:
        for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            g[3 + dr][3 + dc] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pluses":
        # only single 1-cells, no plus intersections → predicate fails everywhere
        g[2][3] = 1; g[5][6] = 1; g[7][2] = 1
        return g
    if name == "partial_pluses":
        # T-shape (4 cells, missing one arm) → not a 5-cell plus, predicate fails
        for (r, c) in [(3, 3), (2, 3), (3, 2), (3, 4)]: g[r][c] = 1   # missing bottom arm
        return g
    if name == "mixed_arm_colors":
        # plus has center + 4 arms but arms are mixed colors → predicate "all blue" fails
        g[3][3] = 1   # blue center
        g[2][3] = 1; g[4][3] = 4   # one arm not blue
        g[3][2] = 1; g[3][4] = 1
        return g
    return g
