"""Generator for arc_puzzle_bank_eleventh_21_bundle:easy_73_crop_nonzero_bounding_box.

Rule: crop the grid to the minimal nonzero bounding box.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_h, motif_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motif, full_grid_motif, multiple_motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd93f1d51f8b"
VERSION = "2.1.1"  # strengthen embedded-crop self_check invariants
TASK_ID = "fd93f1d51f8b"

SUMMARY = (
    "0-bg grid (h ∈ 8-10, w ∈ 9-12) "
    "with: ONE SMALL MOTIF of "
    "DIMENSIONS mh × mw (mh ∈ 2-4, "
    "mw ∈ 2-5) embedded at a random "
    "INTERIOR position (top ∈ "
    "1..h-mh-1, left ∈ 1..w-mw-1) "
    "with ≥1-CELL MARGIN of 0s all "
    "around. The motif's CORNER "
    "CELLS (0,0) and (mh-1, mw-1) "
    "are always painted (so the bbox "
    "is well-defined). Additional "
    "interior cells of the motif "
    "painted randomly in 1-3 "
    "DISTINCT non-bg colors drawn "
    "from {1..9}. Some motif "
    "interior cells may stay 0. "
    "Rule (CROP THE GRID TO THE "
    "MINIMAL BOUNDING BOX "
    "CONTAINING ALL NON-BG CELLS): "
    "COMPUTE the BOUNDING BOX of "
    "all non-bg cells (rmin, cmin, "
    "rmax, cmax). EXTRACT the "
    "subgrid g[rmin..rmax]"
    "[cmin..cmax]. OUTPUT this "
    "cropped subgrid. Net: the "
    "surrounding 0-border is "
    "stripped; only the embedded "
    "motif remains, preserving "
    "its internal pattern."
)

INVARIANTS = [
    "background is 0",
    "one nonzero motif sits strictly inside a larger canvas",
    "output is the motif's nonzero bounding box",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motif", "full_grid_motif", "multiple_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-10 easy / 10-16 med / 14-22 hard", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 11-18 med / 16-24 hard", "valid": "5..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motif_h":        {"type": "int", "default": "2-4 easy / 3-7 med / 5-12 hard (<= h-2)", "valid": "1..20"},
    "motif_w":        {"type": "int", "default": "2-5 easy / 3-9 med / 5-14 hard (<= w-2)", "valid": "1..22"},
    "palette_size":   {"type": "int", "default": "rng 1..6", "valid": "1..9"},
    "fill_density":   {"type": "float", "default": "rng 0.4..0.9 of interior", "valid": "0..1"},
    "position_bias":  {"type": "str", "default": "embedded_motif_with_margin",
                       "valid": "embedded_motif_with_margin"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        mh = min(ctx.draw_int("motif_h", 2, 4), h - 2)
        mw = min(ctx.draw_int("motif_w", 2, 5), w - 2)
        n_col = ctx.draw_int("n_colors", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 22)
        w = ctx.draw_int("grid_w", 16, 24)
        mh = min(ctx.draw_int("motif_h", 5, 12), h - 2)
        mw = min(ctx.draw_int("motif_w", 5, 14), w - 2)
        n_col = ctx.draw_int("n_colors", 2, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 16)
        w = ctx.draw_int("grid_w", 11, 18)
        mh = min(ctx.draw_int("motif_h", 3, 7), h - 2)
        mw = min(ctx.draw_int("motif_w", 3, 9), w - 2)
        n_col = ctx.draw_int("n_colors", 1, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    top = rng.randint(1, h - mh - 1)
    left = rng.randint(1, w - mw - 1)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=min(n_col, 9))

    # The forced corners (0,0) and (mh-1, mw-1) pin the bbox to exactly mh x mw, so the
    # crop output is the full motif rectangle. The interior is filled at a varied
    # density (some cells stay 0), each painted in one of the chosen colors.
    cells = {(0, 0), (mh - 1, mw - 1)}
    density = rng.uniform(0.4, 0.9)
    for r in range(mh):
        for c in range(mw):
            if rng.random() < density:
                cells.add((r, c))
    for r, c in cells:
        g[top + r][left + c] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_motif":
        # blank → no nonzero bbox, rule undefined
        return g
    if name == "full_grid_motif":
        # bbox spans whole grid → rule is identity
        for r in range(h):
            g[r][0] = 4; g[r][w - 1] = 6
        for c in range(w):
            g[0][c] = 3; g[h - 1][c] = 8
        return g
    if name == "multiple_motifs":
        # multiple separated motifs → bbox includes empty space between them
        g[1][1] = 4; g[1][2] = 4
        g[6][7] = 6; g[6][8] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the nonzero motif has a strict surrounding zero border."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    h, w = len(grid), len(grid[0])
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        return ["no non-bg motif cells found"]
    rmin = min(r for r, _c in nz)
    rmax = max(r for r, _c in nz)
    cmin = min(c for _r, c in nz)
    cmax = max(c for _r, c in nz)
    if rmin == 0 or cmin == 0 or rmax == h - 1 or cmax == w - 1:
        errs.append("motif bbox is not strictly inside the canvas")
    if rmax - rmin + 1 < 2 or cmax - cmin + 1 < 2:
        errs.append("motif bbox should be at least 2x2 in normal examples")
    if grid[rmin][cmin] == 0 or grid[rmax][cmax] == 0:
        errs.append("motif bbox corners are not pinned by nonzero cells")
    border_cells = ([(0, c) for c in range(w)] + [(h - 1, c) for c in range(w)] +
                    [(r, 0) for r in range(h)] + [(r, w - 1) for r in range(h)])
    if any(grid[r][c] != 0 for r, c in border_cells):
        errs.append("canvas border should stay background 0")
    return errs
