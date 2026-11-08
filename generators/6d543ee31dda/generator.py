"""Generator for 11b:hard_77 — cross product intersection gallery.

Rule: 6-frames sorted by col give 'column shapes'; 7-frames sorted by
row give 'row shapes'. Output gallery: per (row-shape, col-shape) pair,
the cell-wise AND of their binary masks colored 8, hstack/vstack with
1-cell gaps.

Combinatorial axes (8): ih, iw, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_6_frames, no_7_frames, mismatched_dims.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6d543ee31dda"
VERSION = "2.0.0"
TASK_ID = "6d543ee31dda"
SUMMARY = (
    "0-bg grid containing 2 hollow color-6 FRAMES (placed at "
    "distinct columns, same row band) and 2 hollow color-7 "
    "FRAMES (placed at distinct rows, same column band). All 4 "
    "frames have IDENTICAL interior dimensions (ih × iw, ~4-6 "
    "each). Each frame's interior holds 3-6 non-bg cells in a "
    "single non-{0,6,7} color (the interior pattern). Frames "
    "don't overlap. Rule: sort 6-frames by column → COLUMN "
    "SHAPES (binary interior masks). Sort 7-frames by row → ROW "
    "SHAPES. For each (row-shape, col-shape) pair, compute cell-"
    "wise AND of their masks → paint with color 8. Build "
    "gallery: hstack horizontally for each row shape with 1-col "
    "gap, then vstack the rows with 1-row gap."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 hollow color-6 frames at distinct columns (same row band)",
    "exactly 2 hollow color-7 frames at distinct rows (same column band)",
    "all 4 frames have identical interior dimensions (ih × iw)",
    "each frame interior has 3-6 cells in one non-{0,6,7} color",
    "frames don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_6_frames", "no_7_frames", "mismatched_dims")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "ih":             {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "iw":             {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "position_bias":  {"type": "str", "default": "two_6_two_7_frames",
                       "valid": "two_6_two_7_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 5..7", "valid": "4..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place_frame(g, rng, r0, c0, fh, fw, frame_color, inner_color):
    for c in range(c0, c0 + fw): g[r0][c] = frame_color; g[r0 + fh - 1][c] = frame_color
    for r in range(r0, r0 + fh): g[r][c0] = frame_color; g[r][c0 + fw - 1] = frame_color
    cells = [(r, c) for r in range(r0 + 1, r0 + fh - 1)
             for c in range(c0 + 1, c0 + fw - 1)]
    n = rng.randint(3, 6)
    for r, c in rng.sample(cells, n):
        g[r][c] = inner_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        ih = ctx.draw_int("ih", 4, 4)
        iw = ctx.draw_int("iw", 4, 4)
    elif difficulty == "hard":
        ih = ctx.draw_int("ih", 5, 6)
        iw = ctx.draw_int("iw", 5, 6)
    else:
        ih = ctx.draw_int("ih", 4, 5)
        iw = ctx.draw_int("iw", 4, 5)
    rng = ctx.draw_rng("layout")
    fh = ih + 2; fw = iw + 2
    h = 3 * fh + 4
    w = 3 * fw + 5
    for _ in range(40):
        g = full_grid(h, w, 0)
        inner_palette = rng.sample([1, 2, 3, 4, 5, 8, 9], 4)
        configs = [
            (6, inner_palette[0], 1, 1),
            (6, inner_palette[1], 1, fw + 3),
            (7, inner_palette[2], fh + 2, 1),
            (7, inner_palette[3], fh + 2, fw + 3),
        ]
        ok = True
        for frame_color, inner_color, r0, c0 in configs:
            if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1):
                ok = False; break
            _place_frame(g, rng, r0, c0, fh, fw, frame_color, inner_color)
        if ok:
            return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify 4-frame layout invariants for 6d543ee31dda."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if 6 not in flat:
        errs.append("color 6 (horizontal frame color) not present")
    if 7 not in flat:
        errs.append("color 7 (vertical frame color) not present")
    if flat.count(0) == 0:
        errs.append("no background (0) cells")
    return errs


def _draw_from_degenerate(name, rng):
    fh = fw = 6
    h = 3 * fh + 4; w = 3 * fw + 5
    g = full_grid(h, w, 0)
    if name == "no_6_frames":
        # Only 7-frames — rule has no column shapes for the cross-product.
        _place_frame(g, rng, 1, 1, fh, fw, 7, 4)
        _place_frame(g, rng, 1, fw + 3, fh, fw, 7, 5)
        return g
    if name == "no_7_frames":
        # Only 6-frames — rule has no row shapes.
        _place_frame(g, rng, 1, 1, fh, fw, 6, 4)
        _place_frame(g, rng, 1, fw + 3, fh, fw, 6, 5)
        return g
    if name == "mismatched_dims":
        # 6-frames are 4x4, 7-frames are 6x6 — interior dims don't match for AND.
        for c in range(1, 5): g[1][c] = 6; g[4][c] = 6
        for r in range(1, 5): g[r][1] = 6; g[r][4] = 6
        for c in range(1, 7): g[8][c] = 7; g[13][c] = 7
        for r in range(8, 14): g[r][1] = 7; g[r][6] = 7
        return g
    return g
