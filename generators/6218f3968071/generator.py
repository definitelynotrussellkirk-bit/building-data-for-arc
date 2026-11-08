"""Generator for arc_additional_puzzle_bank_volume10:M68 — Mark interior intersection of 1-cols and 2-rows.

Rule: marker bbox = bbox of {1,2,4} cells. Inside that bbox: cells where
row has a 2 in left col AND col has a 1 in top row → 3.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_ones,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_top_ones, no_left_twos.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6218f3968071"
VERSION = "3.1.0"  # shape-locked in/out: hardcoded 11x11 + fixed frame (3,2,8,7). Rule is size-generic (bbox from {1,2,4} markers; intersections of top-1 cols x left-2 rows -> 3). Now vary grid size + frame bounds + marker counts.
TASK_ID = "6218f3968071"
SUMMARY = (
    "11×11 0-bg grid with: (a) one color-4 rectangular frame outline "
    "with TOP row at r0, BOTTOM at r1, LEFT col at c0, RIGHT at c1; "
    "(b) 1-3 color-1 markers on the TOP edge at interior columns "
    "(replacing some 4s); (c) 1-2 color-2 markers on the LEFT edge at "
    "interior rows; (d) optionally a few decoy cells in other colors "
    "(preserved by rule). Rule: find bbox of {1, 2, 4} cells. Inside "
    "bbox, for each interior cell (r, c): if g[r][c0] == 2 (row has "
    "left-2) AND g[r0][c] == 1 (col has top-1), set to color 3. Else "
    "preserve."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one color-4 frame outline (surrounding interior)",
    "1-3 color-1 markers on top edge",
    "1-2 color-2 markers on left edge",
    "interior of frame is initially 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_top_ones", "no_left_twos")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..16", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_ones":         {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "n_twos":         {"type": "int", "default": "rng 1..2", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "frame_with_top_ones_left_twos",
                       "valid": "frame_with_top_ones_left_twos"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # vary grid size AND frame bounds (rule is size-generic; bbox comes from the
    # color-{1,2,4} markers, intersections of top-1 cols and left-2 rows -> 3)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11); fmin = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20); fmin = 7
    else:
        h = ctx.draw_int("grid_h", 10, 16); w = ctx.draw_int("grid_w", 10, 16); fmin = 6
    g = full_grid(h, w, 0)
    fh = rng.randint(fmin, h - 2); fw = rng.randint(fmin, w - 2)
    r0 = rng.randint(1, h - fh - 1); c0 = rng.randint(1, w - fw - 1)
    r1 = r0 + fh - 1; c1 = c0 + fw - 1
    for c in range(c0, c1 + 1):
        g[r0][c] = 4; g[r1][c] = 4
    for r in range(r0, r1 + 1):
        g[r][c0] = 4; g[r][c1] = 4
    # color-1 markers on the TOP edge (interior cols), color-2 on the LEFT edge
    cols_avail = list(range(c0 + 1, c1)); rng.shuffle(cols_avail)
    rows_avail = list(range(r0 + 1, r1)); rng.shuffle(rows_avail)
    n_ones = rng.randint(1, max(1, min(4, len(cols_avail))))
    n_twos = rng.randint(1, max(1, min(4, len(rows_avail))))
    for c in cols_avail[:n_ones]:
        g[r0][c] = 1
    for r in rows_avail[:n_twos]:
        g[r][c0] = 2
    # color-8 decoy (canonical includes such noise; rule ignores non-{1,2,4})
    if r1 + 1 < h and c1 + 2 < w:
        g[r1 + 1][c1 + 2] = 8
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # 1s and 2s exist but no 4-frame → bbox undefined
        g[3][4] = 1
        g[5][2] = 2
        return g
    if name == "no_top_ones":
        # frame and left-2s but no top-1s → no col-anchor for intersection
        r0, c0, r1, c1 = 3, 2, 8, 7
        for c in range(c0, c1 + 1):
            g[r0][c] = 4; g[r1][c] = 4
        for r in range(r0, r1 + 1):
            g[r][c0] = 4; g[r][c1] = 4
        g[5][c0] = 2
        return g
    if name == "no_left_twos":
        # frame and top-1s but no left-2s → no row-anchor for intersection
        r0, c0, r1, c1 = 3, 2, 8, 7
        for c in range(c0, c1 + 1):
            g[r0][c] = 4; g[r1][c] = 4
        for r in range(r0, r1 + 1):
            g[r][c0] = 4; g[r][c1] = 4
        g[r0][4] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    marker_cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in {1, 2, 4}]
    if not marker_cells:
        return ["expected a marker frame using colors 1, 2, and 4"]
    r0 = min(r for r, _ in marker_cells); r1 = max(r for r, _ in marker_cells)
    c0 = min(c for _, c in marker_cells); c1 = max(c for _, c in marker_cells)
    if r1 - r0 < 4 or c1 - c0 < 4:
        msgs.append("marker bbox must have a real interior")
    top_ones = [c for c in range(c0 + 1, c1) if grid[r0][c] == 1]
    left_twos = [r for r in range(r0 + 1, r1) if grid[r][c0] == 2]
    if not top_ones:
        msgs.append("top edge must contain at least one color-1 column marker")
    if not left_twos:
        msgs.append("left edge must contain at least one color-2 row marker")
    for c in range(c0, c1 + 1):
        if grid[r0][c] not in {1, 4} or grid[r1][c] != 4:
            msgs.append("top/bottom marker-frame edges must be 4 except top 1-markers")
            break
    for r in range(r0, r1 + 1):
        if grid[r][c0] not in {2, 4} or grid[r][c1] != 4:
            msgs.append("left/right marker-frame edges must be 4 except left 2-markers")
            break
    if any(grid[r][c] != 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
        msgs.append("frame interior must be empty before intersections are painted")
    return msgs
