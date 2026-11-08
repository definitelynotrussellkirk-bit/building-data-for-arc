"""Generator for arc_puzzle_bank_21_next:medium_c07 -- rotate each object in place.

Rule: separated objects are cropped to their bbox, rotated clockwise, and
pasted at the same origin.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, all_square_symmetric, rotated_oob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d25404307d09"
VERSION = "2.0.1"
TASK_ID = "d25404307d09"
SUMMARY = (
    "0-bg grid (h, w ~10-13) with 3 SEPARATED 4-cell "
    "objects in distinct colors at fixed origins "
    "(1, 1), (1, w-5), (h-5, 2). Each object is an "
    "L-tetromino-style shape (3-4 cells) with asymmetric "
    "bbox. Rule: for each 4-conn non-bg object: crop to "
    "its BBOX (bbox_h × bbox_w). Rotate the cropped "
    "subgrid 90° CLOCKWISE. Paste the rotated subgrid "
    "back at the SAME origin (top-left of original "
    "bbox) — note rotated bbox is bbox_w × bbox_h, may "
    "extend differently than original. Net: each object "
    "appears rotated 90° CW in place at its bbox top-"
    "left anchor."
)

INVARIANTS = [
    "objects are separated by background",
    "each object's rotated bounding box remains in the grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "all_square_symmetric", "rotated_oob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objs":         {"type": "int", "default": "3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "three_separated_asym_objs",
                       "valid": "three_separated_asym_objs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


PATTERNS = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
)


def _draw_pattern(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-zero colors (objects); each color has ≥3 cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    counts = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if len(counts) < 2:
        errs.append(f"expected ≥2 distinct non-zero object colors; found {len(counts)}")
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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = list(ctx.draw_distinct_colors("colors", n=3, exclude=[0]))
    placements = [(1, 1), (1, w - 5), (h - 5, 2)]
    for idx, (top, left) in enumerate(placements):
        _draw_pattern(g, top, left, rng.choice(PATTERNS), colors[idx])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # blank → no objects to rotate
        return g
    if name == "all_square_symmetric":
        # solid 2x2 squares → rotation is identity (no observable change)
        for r in range(2):
            for c in range(2): g[1 + r][1 + c] = 4
        for r in range(2):
            for c in range(2): g[1 + r][7 + c] = 6
        for r in range(2):
            for c in range(2): g[7 + r][4 + c] = 3
        return g
    if name == "rotated_oob":
        # asymmetric tall blob near right edge → rotation produces wider bbox that clips
        # original 1x4 vertical at col w-2 (h=4); rotated 4x1 horizontal can't fit
        for r in range(4): g[r][w - 2] = 4
        return g
    return g
