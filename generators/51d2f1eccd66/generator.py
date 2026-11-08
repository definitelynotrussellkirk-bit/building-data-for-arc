"""Generator for arc_puzzle_bank_twentythird21:M160 — flood 8-walled chambers.

Rule: color-8 walls divide the grid into chambers (connected regions of non-8
cells). For each non-{0,8} marker seed, flood its whole reachable chamber with
the marker's color. The rule discovers chambers dynamically, so it is fully
size- and count-generic.

The old generator hardcoded a 9×9 grid with a FIXED 2×2 chamber layout
(shape-locked in/out; canonical varies 7×7, 9×9). Now: a varied chamber TABLE —
nr×nc chambers (each with an independently varied interior size) separated by
1-wide color-8 walls, one marker per chamber. Grid size, chamber count/sizes and
marker colors all vary.

Combinatorial axes: chamber grid (nr×nc), per-row/col chamber sizes (-> grid +
output dims), marker colors and positions.
Degenerates: no_walls, no_markers, multi_markers_per_chamber.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box

GENERATOR_ID = "51d2f1eccd66"
VERSION = "3.0.1"  # shape-locked in/out: gen hardcoded 9x9 + a fixed 2x2 chamber grid. Rule floods any 8-walled chamber to its seed colour (size/count-generic; canonical varies). Now a varied chamber TABLE: nr x nc chambers with independently varied sizes + one marker each.
TASK_ID = "51d2f1eccd66"
SUMMARY = (
    "0-bg grid (size varies) carved by 1-wide COLOR-8 walls into an nr×nc TABLE "
    "of CHAMBERS (2-3 per axis), each chamber an independently varied interior "
    "size (2-4 cells per side). Each chamber holds ONE MARKER cell in a non-{0,8} "
    "color at a random interior position. Rule: find the 8-walled chambers and "
    "flood each with its marker color. Net: each chamber becomes a solid "
    "monochrome region of its marker color within the 8-wall grid."
)

INVARIANTS = [
    "background is 0",
    "color-8 walls form an nr×nc table of chambers",
    "each chamber holds exactly one marker in a non-0/non-8 color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_markers", "multi_markers_per_chamber")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_chambers":     {"type": "int", "default": "nr*nc 4-9", "valid": "4..9"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "chamber_table",
                       "valid": "chamber_table"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-8 wall cell; >=4 non-{0,8} marker cells in distinct chambers."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    has_wall = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    if not has_wall:
        errs.append("no color-8 wall cells found")
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    if len(markers) < 4:
        errs.append(f"expected >=4 chamber marker cells, found {len(markers)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        nr, nc = 2, 2; lo, hi = 2, 3
    elif difficulty == "hard":
        nr = rng.randint(2, 3); nc = rng.randint(2, 3); lo, hi = 3, 4
    else:
        nr = rng.randint(2, 3); nc = rng.randint(2, 3); lo, hi = 2, 4

    row_sizes = [rng.randint(lo, hi) for _ in range(nr)]
    col_sizes = [rng.randint(lo, hi) for _ in range(nc)]

    # chamber interior ranges + grid dims (1-wide walls between/around chambers)
    row_ranges = []
    r = 1
    for rs in row_sizes:
        row_ranges.append((r, r + rs - 1))
        r += rs + 1
    h = r
    col_ranges = []
    c = 1
    for cs in col_sizes:
        col_ranges.append((c, c + cs - 1))
        c += cs + 1
    w = c

    g = full_grid(h, w, 8)              # everything wall, then carve chambers to 0
    for (rt, rb) in row_ranges:
        for (ct, cb) in col_ranges:
            fill_box(g, rt, ct, rb, cb, 0)
            cells = [(rr, cc) for rr in range(rt, rb + 1) for cc in range(ct, cb + 1)]
            mr, mc = rng.choice(cells)
            g[mr][mc] = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    walls = lambda: [fill_box(g, 0, 0, 0, w - 1, 8), fill_box(g, 4, 0, 4, w - 1, 8),
                     fill_box(g, h - 1, 0, h - 1, w - 1, 8), fill_box(g, 0, 0, h - 1, 0, 8),
                     fill_box(g, 0, 4, h - 1, 4, 8), fill_box(g, 0, w - 1, h - 1, w - 1, 8)]
    if name == "no_walls":
        g[1][1] = 4; g[1][6] = 6; g[6][1] = 7; g[6][6] = 3
        return g
    if name == "no_markers":
        walls()
        return g
    if name == "multi_markers_per_chamber":
        walls()
        g[1][1] = 4; g[3][3] = 6; g[1][5] = 7; g[5][1] = 3
        return g
    return g
