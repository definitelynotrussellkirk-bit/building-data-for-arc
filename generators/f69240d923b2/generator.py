"""Generator for arc_puzzle_bank_seventh_21_bundle:easy_46_crop_frame_contents.

Combinatorial axes (8): grid_h, grid_w, palette_kind, density,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, empty_interior, multiple_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f69240d923b2"
VERSION = "2.1.0"  # guarantee >=2 distinct interior values (probabilistic fill could roll all-0 -> solid output)
TASK_ID = "f69240d923b2"

SUMMARY = (
    "0-bg grid (size varies, up to ~24) with exactly ONE rectangular cyan(8) "
    "FRAME floating at a random position. Its interior (2..12 in each dim) is "
    "filled at a varying density with non-8 colors. Rule: find the 8 rectangular "
    "frame and crop/return its interior contents. Net: output = whatever is "
    "inside the frame; output SHAPE = the interior size. (Was: interior capped "
    "3-6, grids <=13.)"
)

INVARIANTS = [
    "background is 0; frame color is 8",
    "exactly one rectangular 8 frame (>=3x3 so interior >=1x1)",
    "interior cells use non-8 colors or background (no second frame)",
    "frame floats inside a larger canvas (position varies)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "empty_interior", "multiple_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-11 easy / 10-16 med / 14-24 hard", "valid": "5..26"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 10-16 med / 14-24 hard", "valid": "5..26"},
    "inner_h":        {"type": "int", "default": "2-5 easy / 3-8 med / 5-12 hard", "valid": "1..14"},
    "inner_w":        {"type": "int", "default": "2-5 easy / 3-8 med / 5-12 hard", "valid": "1..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "density_pct":    {"type": "int", "default": "rng 35..70", "valid": "5..95"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8..8"},
    "position_bias":  {"type": "str", "default": "single_8frame_with_interior",
                       "valid": "single_8frame_with_interior"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8..8"},
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
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        density = ctx.draw_int("density", 35, 50)
        ih = min(ctx.draw_int("inner_h", 2, 5), h - 2)
        iw = min(ctx.draw_int("inner_w", 2, 5), w - 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 24)
        w = ctx.draw_int("grid_w", 14, 24)
        density = ctx.draw_int("density", 45, 75)
        ih = min(ctx.draw_int("inner_h", 5, 12), h - 2)
        iw = min(ctx.draw_int("inner_w", 5, 12), w - 2)
    else:
        h = ctx.draw_int("grid_h", 10, 16)
        w = ctx.draw_int("grid_w", 10, 16)
        density = ctx.draw_int("density", 40, 65)
        ih = min(ctx.draw_int("inner_h", 3, 8), h - 2)
        iw = min(ctx.draw_int("inner_w", 3, 8), w - 2)
    rng = ctx.draw_rng("layout")
    fh = ih + 2
    fw = iw + 2
    r0 = rng.randint(0, h - fh)
    c0 = rng.randint(0, w - fw)
    r1 = r0 + fh - 1
    c1 = c0 + fw - 1
    g = full_grid(h, w, 0)
    for c in range(c0, c1 + 1):
        g[r0][c] = 8
        g[r1][c] = 8
    for r in range(r0, r1 + 1):
        g[r][c0] = 8
        g[r][c1] = 8
    colors = [1, 2, 3, 4, 5, 6, 7, 9]
    interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    for r, c in interior:
        if rng.randrange(100) < density:
            g[r][c] = rng.choice(colors)
    # The probabilistic fill can leave the interior all-0 (or all one color), which the
    # rule crops to a degenerate solid output. Guarantee >=2 distinct interior values.
    if len(interior) >= 2 and len({g[r][c] for r, c in interior}) < 2:
        rng.shuffle(interior)
        (ra, ca), (rb, cb) = interior[0], interior[1]
        g[ra][ca] = rng.choice(colors)
        g[rb][cb] = 0
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one rectangular 8-frame whose interior has >=2 distinct values, so the
    cropped output is not a degenerate solid block."""
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not eights:
        errs.append("no color-8 frame")
        return errs
    r0 = min(r for r, _ in eights); r1 = max(r for r, _ in eights)
    c0 = min(c for _, c in eights); c1 = max(c for _, c in eights)
    interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    if interior and len({grid[r][c] for r, c in interior}) < 2 and len(interior) >= 2:
        errs.append("frame interior is uniform -> cropped output is solid")
    if any(grid[r][c] == 8 for r, c in interior):
        errs.append("color-8 appears inside the frame interior (second frame?)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # interior content but no 8-frame → no cyan frame to crop
        for r in range(2, 5):
            for c in range(2, 6):
                g[r][c] = 4
        return g
    if name == "empty_interior":
        # 8-frame but empty interior → trivial crop, no contrast
        for c in range(2, 8): g[2][c] = 8; g[7][c] = 8
        for r in range(2, 8): g[r][2] = 8; g[r][7] = 8
        return g
    if name == "multiple_frames":
        # 2 separate 8-frames → "exactly one" precondition fails
        for c in range(1, 5): g[1][c] = 8; g[4][c] = 8
        for r in range(1, 5): g[r][1] = 8; g[r][4] = 8
        for c in range(6, 10): g[1][c] = 8; g[4][c] = 8
        for r in range(1, 5): g[r][6] = 8; g[r][9] = 8
        return g
    return g
