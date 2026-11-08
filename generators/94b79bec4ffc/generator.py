"""Generator for arc_puzzle_bank_21_set17_bundle:easy_p02.

Rows are marked on the left or right border to dock their colored segment.

Combinatorial axes (8): grid_h, grid_w, palette_kind, row_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_segment, marker_at_both_edges.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "94b79bec4ffc"
VERSION = "2.1.0"  # add row-docking self_check; metadata now matches marker-removal rule
TASK_ID = "94b79bec4ffc"
SUMMARY = (
    "0-bg grid (h ∈ 6-9, w ∈ 9-13) with: "
    "ROW_COUNT ∈ 3-5 ACTIVE ROWS, "
    "each with: (a) ONE ROW MARKER at "
    "EITHER LEFT EDGE (col 0, color 1) "
    "OR RIGHT EDGE (col w-1, color 2) "
    "— chosen randomly per row; "
    "(b) ONE COLORED SEGMENT of "
    "length 2-min(5, w-3) painted in "
    "a distinct color drawn from "
    "{3..9}\\{1, 2}, placed at a "
    "random middle column position "
    "(NOT at the same edge as the "
    "marker). Inactive rows stay "
    "all-0. Rule (FOR EACH MARKED "
    "ROW, DOCK ITS COLORED SEGMENT "
    "AGAINST THE MARKER'S EDGE — "
    "MARKER=1 (LEFT) → SEGMENT "
    "MOVES LEFT TO TOUCH COL 0 "
    "(JUST AFTER MARKER); MARKER=2 "
    "(RIGHT) → SEGMENT MOVES RIGHT "
    "TO TOUCH COL W-1): For EACH "
    "row with a marker: CLEAR the "
    "segment's current cells to 0. "
    "REPLACE with the segment "
    "STARTING at col 1 (if marker "
    "is at left/color 1) OR ENDING "
    "at col w-2 (if marker is at "
    "right/color 2). The marker "
    "stays at its edge. Net: each "
    "row's segment is pulled "
    "toward the row's edge-marker, "
    "docking against it."
)

INVARIANTS = [
    "background is 0",
    "row marker 1 appears only at the left edge",
    "row marker 2 appears only at the right edge",
    "segment colors exclude marker colors 1 and 2",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_segment", "marker_at_both_edges")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "row_count":      {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "marked_rows_with_segment",
                       "valid": "marked_rows_with_segment"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..7"},
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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 11)
        row_count = min(ctx.draw_int("row_count", 3, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 13)
        row_count = min(ctx.draw_int("row_count", 4, 5), h)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 9, 13)
        row_count = min(ctx.draw_int("row_count", 3, 5), h)
    colors = ctx.draw_distinct_colors("colors", n=row_count, exclude={0, 1, 2})
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), row_count)
    for i, r in enumerate(rows):
        length = rng.randint(2, min(5, w - 3))
        if rng.choice([True, False]):
            g[r][0] = 1
            start = rng.randint(2, w - length - 1)
        else:
            g[r][w - 1] = 2
            start = rng.randint(1, w - length - 3)
        for c in range(start, start + length):
            g[r][c] = colors[i]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h, w = len(grid), len(grid[0])
    marked = 0
    for r, row in enumerate(grid):
        left = row[0] == 1
        right = row[-1] == 2
        if left and right:
            errs.append(f"row {r} has both left and right markers")
        if not left and not right:
            if any(v != 0 for v in row):
                errs.append(f"row {r} has a segment but no dock marker")
            continue
        marked += 1
        seg_cells = [(c, v) for c, v in enumerate(row) if v not in (0, 1, 2)]
        if not seg_cells:
            errs.append(f"row {r} has a marker but no segment")
            continue
        colors = {v for _, v in seg_cells}
        if len(colors) != 1:
            errs.append(f"row {r} segment has multiple colors {sorted(colors)}")
        cols = [c for c, _ in seg_cells]
        if cols != list(range(min(cols), max(cols) + 1)):
            errs.append(f"row {r} segment is not contiguous: {cols}")
        if left and min(cols) <= 1:
            errs.append(f"row {r} left-marker segment already touches the dock edge")
        if right and max(cols) >= w - 2:
            errs.append(f"row {r} right-marker segment already touches the dock edge")
    if marked < 3:
        errs.append(f"expected at least 3 marked teaching rows, found {marked}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # segment without row marker → no dock direction specified
        for c in range(3, 7): g[2][c] = 4
        return g
    if name == "no_segment":
        # marker without segment → nothing to dock
        g[2][0] = 1
        g[4][w - 1] = 2
        return g
    if name == "marker_at_both_edges":
        # row has both 1 and 2 markers → ambiguous dock direction
        g[2][0] = 1; g[2][w - 1] = 2
        for c in range(3, 7): g[2][c] = 4
        return g
    return g
