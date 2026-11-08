"""Generator for v3_rich_schema:hard_04_row_col_intersections_within_bbox.

Rule: paint cyan at every (red-row x blue-col) intersection that lies
STRICTLY inside the gray frame's bbox.

Combinatorial axes: grid_h/w, frame position+size, red-row / blue-col
subsets (inside the frame -> cyan), decoy markers outside, colors.
Degenerates: no_frame, no_markers, all_intersections_outside.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "19496da22435"
VERSION = "3.0.2"  # diversity: random grid + frame placement + random marker/decoy subsets (was fixed 10x12 + 6 layouts)
TASK_ID = "19496da22435"
SUMMARY = (
    "0-bg grid (h,w vary by difficulty). A color-7 (orange) hollow "
    "RECTANGULAR FRAME at a RANDOM position/size. ROW 0 holds BLUE "
    "(color 1) COLUMN markers; COL 0 holds RED (color 2) ROW markers. "
    "Some markers sit on columns/rows that are STRICTLY INSIDE the "
    "frame (a random subset of interior cols/rows) and some are DECOYS "
    "on cols/rows outside the frame. Rule (FILL ROW x COL INTERSECTIONS "
    "INSIDE THE FRAME): take the frame bbox; for each blue-marked col c "
    "and red-marked row r with the intersection (r,c) strictly inside "
    "the frame, paint (r,c) color 8 (cyan). Decoy intersections (one or "
    "both markers outside) stay empty. Grid size, frame placement, the "
    "interior marker lattice and the decoys all vary freely (was a "
    "fixed 10x12 grid with 6 hardcoded layouts)."
)

INVARIANTS = [
    "top-row color-1 markers identify candidate columns",
    "left-column color-2 markers identify candidate rows",
    "a color-7 rectangular frame bounds valid intersections",
    "only strict interior intersections are filled with color 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_markers", "all_intersections_outside")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14 (easy 8..10, hard 12..16)", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 11..15 (easy 10..12, hard 13..18)", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "variant":        {"type": "int", "default": "n/a (now random subsets)", "valid": "0..5"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "framed_grid",
                       "valid": "framed_grid"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frame|no_markers|all_intersections_outside"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify markers plus one color-7 rectangular frame with interior intersections."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    col_markers = [c for c in range(1, w) if grid[0][c] == 1]
    row_markers = [r for r in range(1, h) if grid[r][0] == 2]
    if not col_markers:
        errs.append("no color-1 column markers in row 0")
    if not row_markers:
        errs.append("no color-2 row markers in col 0")
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    if not sevens:
        errs.append("no color-7 frame cells found")
        return errs
    rs = [r for r, _ in sevens]; cs = [c for _, c in sevens]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    border = {(r0, c) for c in range(c0, c1 + 1)} | {(r1, c) for c in range(c0, c1 + 1)} | {(r, c0) for r in range(r0, r1 + 1)} | {(r, c1) for r in range(r0, r1 + 1)}
    if set(sevens) != border:
        errs.append("color-7 cells are not exactly one hollow rectangular frame")
    inside_rows = [r for r in row_markers if r0 < r < r1]
    inside_cols = [c for c in col_markers if c0 < c < c1]
    if not inside_rows or not inside_cols:
        errs.append("no marked row/column pair intersects strictly inside the frame")
    for r in inside_rows:
        for c in inside_cols:
            if grid[r][c] != 0:
                errs.append("expected marked interior intersection to start as background")
                return errs
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 10, 12)
        n_red, n_blue, n_decoy = (1, 2), (1, 2), (1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 13, 18)
        n_red, n_blue, n_decoy = (2, 4), (2, 4), (2, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 15)
        n_red, n_blue, n_decoy = (1, 3), (1, 3), (1, 3)

    g = full_grid(h, w, 0)

    # Random frame: top-left in the upper-left region, big enough that its
    # strict interior holds >=2 rows and >=2 cols (so a lattice is possible).
    # r0>=1, c0>=1 keep the frame clear of the marker strips (row 0, col 0).
    r0 = rng.randint(1, max(1, h - 6))
    c0 = rng.randint(1, max(1, w - 6))
    r1 = rng.randint(r0 + 3, h - 1)
    c1 = rng.randint(c0 + 3, w - 1)
    draw_frame(g, r0, c0, r1, c1, 7)

    interior_rows = list(range(r0 + 1, r1))
    interior_cols = list(range(c0 + 1, c1))

    # Choose which interior rows/cols carry markers -> these cross to cyan.
    nr = min(rng.randint(*n_red), len(interior_rows))
    nc = min(rng.randint(*n_blue), len(interior_cols))
    red_rows = rng.sample(interior_rows, max(1, nr))
    blue_cols = rng.sample(interior_cols, max(1, nc))

    # Decoys: markers on rows/cols NOT strictly inside the frame -> no cyan.
    decoy_rows = [r for r in range(1, h) if not (r0 < r < r1)]
    decoy_cols = [c for c in range(1, w) if not (c0 < c < c1)]
    rng.shuffle(decoy_rows); rng.shuffle(decoy_cols)
    dr = min(rng.randint(*n_decoy), len(decoy_rows))
    dc = min(rng.randint(*n_decoy), len(decoy_cols))

    for r in red_rows + decoy_rows[:dr]:
        g[r][0] = 2
    for c in blue_cols + decoy_cols[:dc]:
        g[0][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_frame":
        # no color-7 frame → no bounding box, all intersections look valid
        for c in [4, 7, 10]:
            g[0][c] = 1
        for r in [3, 5, 8]:
            g[r][0] = 2
        return g
    if name == "no_markers":
        # frame exists but no row/col markers → no intersections to compute
        draw_frame(g, 2, 3, 7, 9, 7)
        return g
    if name == "all_intersections_outside":
        # every marker pair intersects outside the frame → interior filter empties
        draw_frame(g, 2, 3, 7, 9, 7)
        for c in [10, 11]:
            g[0][c] = 1
        for r in [8, 9]:
            g[r][0] = 2
        return g
    return g
