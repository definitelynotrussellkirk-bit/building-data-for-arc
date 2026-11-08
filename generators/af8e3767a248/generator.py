"""Generator for arc_additional_puzzle_bank_volume9:M58.

The overlap of blue- and red-corner implied rectangles is filled green.

Combinatorial axes (8): grid_h, grid_w, palette_kind, overlap_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blue, no_red, no_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af8e3767a248"
VERSION = "1.1.1"
TASK_ID = "af8e3767a248"
SUMMARY = "The overlap of blue- and red-corner implied rectangles is filled green."

INVARIANTS = [
    "background is 0",
    "there are exactly two blue markers and exactly two red markers",
    "same-color marker pairs are opposite rectangle corners",
    "the two implied rectangles have a nonempty overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blue", "no_red", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "overlap_size":   {"type": "str", "default": "rng small|med|large",
                       "valid": "small|med|large"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_overlapping_rects",
                       "valid": "two_overlapping_rects"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly 2 blue (1) and exactly 2 red (2) marker cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_blue", "no_red"):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    blues = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    reds = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    if blues != 2:
        errs.append(f"expected exactly 2 blue (1) markers; found {blues}")
    if reds != 2:
        errs.append(f"expected exactly 2 red (2) markers; found {reds}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 8, 14)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    br1 = rng.randint(0, h // 3)
    bc1 = rng.randint(0, w // 3)
    br2 = rng.randint((2 * h) // 3, h - 1)
    bc2 = rng.randint((2 * w) // 3, w - 1)
    blue = {(br1, bc1), (br2, bc2)}
    rr1 = rc1 = rr2 = rc2 = 0
    for _ in range(80):
        rr1 = rng.randint(1, max(1, h // 2))
        rc1 = rng.randint(1, max(1, w // 2))
        rr2 = rng.randint(max(rr1 + 1, h // 2), h - 2)
        rc2 = rng.randint(max(rc1 + 1, w // 2), w - 2)
        if (rr1, rc1) not in blue and (rr2, rc2) not in blue:
            break
    for r, c in [(br1, bc1), (br2, bc2)]:
        g[r][c] = 1
    for r, c in [(rr1, rc1), (rr2, rc2)]:
        g[r][c] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_blue":
        # only red markers → no blue rectangle, no overlap to compute
        g[2][2] = 2; g[7][7] = 2
        return g
    if name == "no_red":
        # only blue markers → no red rectangle, no overlap
        g[1][1] = 1; g[8][8] = 1
        return g
    if name == "no_overlap":
        # rectangles disjoint → overlap is empty (rule has no effect)
        g[0][0] = 1; g[2][2] = 1
        g[6][6] = 2; g[8][8] = 2
        return g
    return g
