"""Generator for ARC task 952a094c.

Rule: a single solid rectangle of one color in a uniform-color grid;
the four inside-corner cells of the rectangle have four distinct
non-rect colors. The rule clears those marker cells to background 0 and
places their colors at the corresponding diagonally-opposite OUTSIDE corners.

Invariants — see INVARIANTS list.

This is the worked-example puzzle in docs/PUZZLE_GENERATOR_SPEC.md.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "e6cf1120a17d"
VERSION = "3.2.0"  # CRITICAL: rule hardcodes bg=0 (filters !=0 then most-frequent = rect-color). Generator drew bg from 0-9 -> when bg!=0 the rule picks bg as the 'rectangle' -> WRONG output (39/40 corrupt). bg now forced to 0 (matches canonical + rule assumption)
TASK_ID = "e6cf1120a17d"
SUMMARY = (
    "BG-colored grid (h ∈ 7-30, w ∈ "
    "7-30, by difficulty) painted "
    "uniformly with one bg color "
    "fixed to 0, containing: "
    "(a) ONE SOLID RECTANGLE of size "
    "rh × rw (rh ∈ 5..h-2, rw ∈ "
    "5..w-2, both ≥5) at random "
    "interior position (rr, rc) with "
    "≥1-cell margin from all grid "
    "edges, painted in rect_color "
    "(distinct from 0). (b) AT THE "
    "RECTANGLE'S FOUR INSIDE-CORNER "
    "CELLS — (rr+1, rc+1), (rr+1, "
    "rc+rw-2), (rr+rh-2, rc+1), "
    "(rr+rh-2, rc+rw-2) — paint 4 "
    "DISTINCT non-{0, rect_color} "
    "colors drawn from {0..9}. Rule "
    "(CLEAR THE FOUR INSIDE CORNERS "
    "(SET TO BACKGROUND 0) AND PLACE "
    "THE 4 CORNER COLORS AT THE "
    "FOUR DIAGONALLY-OPPOSITE "
    "OUTSIDE CORNERS OF THE "
    "RECTANGLE): IDENTIFY the "
    "rectangle (solid rect_color "
    "region) and its 4 inside-"
    "corner cells with their "
    "distinct colors c0, c1, c2, c3 "
    "(TL, TR, BL, BR of inside). "
    "CLEAR the 4 inside-corner marker "
    "cells to background 0, leaving "
    "four holes in the rectangle. "
    "PAINT the 4 OUTSIDE-CORNER "
    "cells of the rectangle: "
    "(rr-1, rc-1)=c3 (diagonally "
    "opposite TL→BR-corner), "
    "(rr-1, rc+rw)=c2 (TR→BL), "
    "(rr+rh, rc-1)=c1 (BL→TR), "
    "(rr+rh, rc+rw)=c0 (BR→TL). "
    "Net: inside colors jump to "
    "the diagonally-opposite "
    "outside corners while their "
    "former cells become background."
)

INVARIANTS = [
    "exactly one rectangle-color region with four inset marker cells",
    "the rectangle's 4 inside-corner cells have 4 distinct non-rect colors",
    "background is uniform color 0, distinct from rect_color and corner colors",
    "rectangle has at least 1 cell of margin from every grid edge",
    "rectangle dimensions: at least 5x5 (so inside-corner cells are well-defined)",
]

AXES = {
    "bg":            {"type": "color",     "default": "0",           "valid": "0"},
    "rect_color":    {"type": "color",     "default": "rng",         "valid": "1..9"},
    "corner_colors": {"type": "colors[4]", "default": "rng_distinct",
                      "valid": "1..9 distinct, != rect_color"},
    # Wider grid range than v1.0.0 — gives the difficulty scorer room to
    # span [easy, hard], including the legal 30×30 boundary.
    "grid_h":        {"type": "int",       "default": "rng 7..30",   "valid": "7..30"},
    "grid_w":        {"type": "int",       "default": "rng 7..30",   "valid": "7..30"},
    "rect_h":        {"type": "int",       "default": "rng 5..h-2",  "valid": ">=5, <= h-2"},
    "rect_w":        {"type": "int",       "default": "rng 5..w-2",  "valid": ">=5, <= w-2"},
    "rect_rr":       {"type": "int",       "default": "rng with margin",
                      "valid": "1..h-rect_h-1"},
    "rect_rc":       {"type": "int",       "default": "rng with margin",
                      "valid": "1..w-rect_w-1"},
    # When `difficulty="easy"|"hard"`, the generator narrows the grid
    # range to the bottom or top half of the legal range. None = full range.
    "difficulty":    {"type": "enum",      "default": "None",
                      "valid": "easy | medium | hard | None"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    bg          = 0   # rule hardcodes bg=0 (filters !=0 to find the rectangle); must be 0
    rect_color  = ctx.draw_color("rect_color", exclude={0})
    corners     = ctx.draw_distinct_colors("corner_colors", n=4,
                                            exclude={0, rect_color})
    # Difficulty narrows the grid range so this one generator naturally
    # spans the score space.
    if difficulty == "easy":
        h_lo, h_hi = 7, 11
    elif difficulty == "hard":
        h_lo, h_hi = 20, 30
    else:
        h_lo, h_hi = 7, 30
    h           = ctx.draw_int("grid_h", h_lo, h_hi)
    w           = ctx.draw_int("grid_w", h_lo, h_hi)
    # A rectangle may occupy every row/column except the required one-cell margin.
    rh          = ctx.draw_int("rect_h", 5, h - 2)
    rw          = ctx.draw_int("rect_w", 5, w - 2)
    rr          = ctx.draw_int("rect_rr", 1, h - rh - 1)
    rc          = ctx.draw_int("rect_rc", 1, w - rw - 1)

    g = full_grid(h, w, bg)
    draw_rect(g, rr, rc, rh, rw, rect_color)
    g[rr + 1     ][rc + 1     ] = corners[0]   # top-left inside
    g[rr + 1     ][rc + rw - 2] = corners[1]   # top-right inside
    g[rr + rh - 2][rc + 1     ] = corners[2]   # bottom-left inside
    g[rr + rh - 2][rc + rw - 2] = corners[3]   # bottom-right inside
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify bg=0, one rectangle-color region, and four distinct inset markers."""
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    counts: dict[int, int] = {}
    for row in grid:
        for v in row:
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return ["no nonzero rectangle/corner colors"]
    rect_color = max(counts, key=counts.get)
    if rect_color == 0:
        errs.append("rectangle color must be nonzero")
    rect_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == rect_color]
    rs = [r for r, _ in rect_cells]; cs = [c for _, c in rect_cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    rh, rw = r1 - r0 + 1, c1 - c0 + 1
    if rh < 5 or rw < 5:
        errs.append(f"rectangle bbox too small: {rh}x{rw}")
    if r0 < 1 or c0 < 1 or r1 >= h - 1 or c1 >= w - 1:
        errs.append("rectangle must have one-cell margin for outside corners")
    expected_holes = {(r0 + 1, c0 + 1), (r0 + 1, c1 - 1), (r1 - 1, c0 + 1), (r1 - 1, c1 - 1)}
    corner_vals = [grid[r][c] for r, c in expected_holes]
    if any(v in (0, rect_color) for v in corner_vals) or len(set(corner_vals)) != 4:
        errs.append(f"inside-corner colors must be four distinct nonzero non-rect values, got {corner_vals}")
    for r in range(h):
        for c in range(w):
            inside = r0 <= r <= r1 and c0 <= c <= c1
            if inside:
                if (r, c) in expected_holes:
                    continue
                if grid[r][c] != rect_color:
                    errs.append("rectangle body must be solid except four inset corner cells")
                    return errs
            elif grid[r][c] != 0:
                errs.append(f"nonzero cell outside rectangle at {(r, c)}")
                return errs
    return errs

