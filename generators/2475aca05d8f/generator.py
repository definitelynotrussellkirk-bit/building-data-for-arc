"""Generator for arc_puzzle_bank_fifth_21_bundle:easy_30_crop_nonzero_bbox.

Rule: crop to the bbox of all nonzero cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_h, motif_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motif, full_grid_motif, multiple_motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import bbox

GENERATOR_ID = "2475aca05d8f"
VERSION = "1.1.1"
TASK_ID = "2475aca05d8f"
SUMMARY = "A small multicolor motif padded by background for crop-to-content."

INVARIANTS = [
    "background is 0",
    "nonzero cells form a compact motif away from the border",
    "the nonzero bbox is strictly smaller than the grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motif", "full_grid_motif", "multiple_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motif_h":        {"type": "int", "default": "rng 2..4", "valid": "2..8"},
    "motif_w":        {"type": "int", "default": "rng 2..4", "valid": "2..8"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "centered_motif_with_margin",
                       "valid": "centered_motif_with_margin"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
    "density":        {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        mh = ctx.draw_int("motif_h", 2, 3)
        mw = ctx.draw_int("motif_w", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        mh = ctx.draw_int("motif_h", 3, 4)
        mw = ctx.draw_int("motif_w", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 8, 12)
        mh = ctx.draw_int("motif_h", 2, min(4, h - 2))
        mw = ctx.draw_int("motif_w", 2, min(4, w - 2))
    colors = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    rr = rng.randint(1, h - mh - 1)
    rc = rng.randint(1, w - mw - 1)
    for r in range(mh):
        for c in range(mw):
            if rng.random() < 0.7 or (r, c) in ((0, 0), (mh - 1, mw - 1)):
                g[rr + r][rc + c] = colors[(r + c) % len(colors)]

    # Some 2x3 / 3x2 motifs have the two forced diagonal cells on the same
    # palette phase; if the probabilistic interior cells all miss, the demo
    # collapses to a single-color crop.  Keep the texture random but fail closed
    # by planting one extra in-bbox cell with a second color.
    motif_colors = {g[rr + r][rc + c] for r in range(mh) for c in range(mw)
                    if g[rr + r][rc + c] != 0}
    if len(motif_colors) < 2:
        for r in range(mh):
            for c in range(mw):
                if (r, c) != (0, 0):
                    g[rr + r][rc + c] = colors[1]
                    return g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_motif":
        # blank → no nonzero bbox, rule undefined
        return g
    if name == "full_grid_motif":
        # nonzero cells span whole grid → crop is identity
        for r in range(h):
            g[r][0] = 4; g[r][w - 1] = 6
        for c in range(w):
            g[0][c] = 3; g[h - 1][c] = 8
        return g
    if name == "multiple_motifs":
        # two separated motifs → bbox spans both, includes empty space between
        g[1][1] = 4; g[1][2] = 4
        g[6][7] = 6; g[6][8] = 6
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for crop-to-nonzero-bbox inputs."""
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows have inconsistent widths"]
    nz = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not nz:
        return ["no nonzero motif cells"]
    r1, c1, r2, c2 = bbox(nz)
    if r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1:
        errs.append(f"nonzero bbox touches border: {(r1, c1, r2, c2)} in {h}x{w}")
    if r1 == 0 and c1 == 0 and r2 == h - 1 and c2 == w - 1:
        errs.append("nonzero bbox spans the whole grid; crop would be identity")
    if len({grid[r][c] for r, c in nz}) < 2:
        errs.append("motif should contain at least two colors")
    return errs
