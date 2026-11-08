"""Generator for ARC task 928ad970.

Rule: 4 color-5 markers + 1 non-5 cell. Output paints inset rectangle
(rows r1+1, r2-1; cols c1+1, c2-1) with the non-5 color.

Combinatorial axes (8): grid_h/w, draw_color, rect_size_kind,
position_bias, marker_position_kind, anchor_inset, n_decoy_pixels,
asymmetry_force.
Degenerates: missing_marker, no_color, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "483d78b1d04b"
VERSION = "2.0.1"
TASK_ID = "483d78b1d04b"
SUMMARY = (
    "0-bg grid (h, w~10-18) "
    "with: (a) EXACTLY 4 "
    "COLOR-5 (gray) MARKERS at "
    "the CORNERS of a "
    "RECTANGLE (r1, c1), (r1, "
    "c2), (r2, c1), (r2, c2) "
    "with r2-r1 ≥ 4, c2-c1 ≥ "
    "4 in one of 5 RECT_SIZE "
    "kinds (small/medium/large/"
    "wide/tall) and 3 POSITION "
    "BIASES (spread/center/"
    "edge); (b) EXACTLY 1 "
    "NON-5 NONZERO CELL at "
    "rectangle CENTER "
    "((r1+r2)//2, (c1+c2)//2) "
    "in a DRAW_COLOR from "
    "{1..9}\\{5}. Rule (PAINT "
    "INSET RECTANGLE OUTLINE "
    "WITH DRAW COLOR): "
    "identify the 4 GRAY "
    "MARKERS (rectangle "
    "corners) and the NON-5 "
    "DRAW COLOR. PAINT the "
    "INSET RECTANGLE OUTLINE — "
    "rows r1+1, r2-1 and "
    "cols c1+1, c2-1 — in the "
    "DRAW COLOR. The 4 gray "
    "markers stay. The center "
    "draw-color cell may be "
    "kept or absorbed. Net: "
    "4 gray corners outline a "
    "rect; rule draws a "
    "hollow inset rect inside "
    "in the marker color."
)

INVARIANTS = [
    "exactly 4 color-5 markers at rectangle corners",
    "exactly one non-5 nonzero cell (the draw color)",
    "inset rectangle has h >= 3 and w >= 3 (so r1+1 < r2-1 isn't trivial)",
    "no other non-bg cells",
]

RECT_SIZE_KINDS = ("small", "medium", "large", "wide", "tall")
DEGENERATE_TEXTURES = ("missing_marker", "no_color", "full_grid")
HELPFUL_TEXTURES = RECT_SIZE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 10..18", "valid": "6..22"},
    "grid_w":            {"type": "int", "default": "rng 10..18", "valid": "6..22"},
    "draw_color":        {"type": "color", "default": "rng (≠0,5)",
                          "valid": "1..9 (≠5)"},
    "rect_size_kind":    {"type": "str", "default": "rng helpful",
                          "valid": "|".join(RECT_SIZE_KINDS)},
    "position_bias":     {"type": "str", "default": "rng spread|center|edge",
                          "valid": "spread|center|edge"},
    "marker_offset_kind": {"type": "str", "default": "rng tight|loose",
                           "valid": "tight|loose"},
    "anchor_inset":      {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for rect_size_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 6, 10
    elif difficulty == "hard":
        h_lo, h_hi = 16, 22
    else:
        h_lo, h_hi = 10, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    color = int(overrides.get("draw_color",
                              ctx.draw_color("draw_color", exclude={0, 5})))
    size_kind = (overrides.get("texture") or
                 overrides.get("rect_size_kind")
                 or ctx.draw_choice("rect_size_kind",
                                    list(RECT_SIZE_KINDS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    r1, r2, c1, c2 = _draw_rect(size_kind, bias, h, w, rng)
    g = full_grid(h, w, 0)
    for r, c in [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]:
        g[r][c] = 5
    g[(r1 + r2) // 2][(c1 + c2) // 2] = color
    if bool(overrides.get("anchor_inset", False)):
        g[r1 + 1][c1 + 1] = color
        g[(r1 + r2) // 2][(c1 + c2) // 2] = color
        # only one non-5 allowed
        for r in range(h):
            for c in range(w):
                if g[r][c] not in (0, 5):
                    g[r][c] = 0
        g[(r1 + r2) // 2][(c1 + c2) // 2] = color
    return g


def _draw_rect(size_kind, bias, h, w, rng):
    if size_kind == "small":
        rh = max(4, min(h - 2, 5))
        rw = max(4, min(w - 2, 5))
    elif size_kind == "large":
        rh = max(6, h - 4)
        rw = max(6, w - 4)
    elif size_kind == "wide":
        rh = max(4, h // 2)
        rw = max(6, w - 3)
    elif size_kind == "tall":
        rh = max(6, h - 3)
        rw = max(4, w // 2)
    else:
        rh = max(5, min(h - 3, h - 4))
        rw = max(5, min(w - 3, w - 4))
    if bias == "center":
        r1 = (h - rh) // 2
        c1 = (w - rw) // 2
    elif bias == "edge":
        r1 = 1; c1 = 1
    else:
        r1 = rng.randint(1, max(1, h - rh - 1))
        c1 = rng.randint(1, max(1, w - rw - 1))
    r2 = r1 + rh - 1
    c2 = c1 + rw - 1
    if r2 >= h:
        r2 = h - 2; r1 = max(1, r2 - rh + 1)
    if c2 >= w:
        c2 = w - 2; c1 = max(1, c2 - rw + 1)
    return r1, r2, c1, c2


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    if name == "missing_marker":
        for r, c in [(2, 2), (2, w - 3), (h - 3, 2)]:
            g[r][c] = 5
        g[h // 2][w // 2] = color
        return g
    if name == "no_color":
        for r, c in [(2, 2), (2, w - 3), (h - 3, 2), (h - 3, w - 3)]:
            g[r][c] = 5
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """exactly 4 color-5 corner markers; exactly 1 non-5 non-0 draw-color cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if len(fives) != 4:
        errors.append(f"expected exactly 4 color-5 markers, found {len(fives)}")
    draw_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if len(draw_cells) != 1:
        errors.append(f"expected exactly 1 non-5 non-0 draw-color cell, found {len(draw_cells)}")
    return errors
