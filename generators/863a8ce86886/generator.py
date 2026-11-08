"""Generator for arc_puzzle_bank_twentysecond21:H149 — replay relative A→B edit onto C.

Rule: transfer a relative support add/remove edit from A->B onto C.

Combinatorial axes (8): grid_h, grid_w, palette_kind, variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_separators, no_panel_a, identical_a_b.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "863a8ce86886"
VERSION = "2.1.1"  # in_sh=out_sh=1: fixed 5x17 (panels 5x5). Rule reads panels via full-8 separator cols and outputs the edited C panel (panel size); canonical 5x5 but the rule is panel-size-generic. Vary panel size PHxPW -> grid PH x (3PW+2), output PHxPW. distinct already 143.
TASK_ID = "863a8ce86886"
SUMMARY = (
    "Fixed 5×17 0-bg grid laid out as THREE 5×5 "
    "PANELS separated by FULL-HEIGHT COLOR-8 "
    "SEPARATOR COLUMNS at cols 5 and 11. Each "
    "panel hosts a 3×3 edit-bbox at random "
    "panel-local top/left position (0..2). "
    "(a) PANEL A (cols 0-4): a random 3×3 mask of "
    "3-6 set cells painted in A_COLOR (from "
    "{1,2,3,4}) at position (a_top, a_left); "
    "(b) PANEL B (cols 6-10): a VARIANT of A — "
    "n_changes (1-4) cells flipped relative to A, "
    "painted in the SAME A_COLOR at the SAME "
    "(a_top, a_left); (c) PANEL C (cols 12-16): "
    "an INDEPENDENT random 3×3 shape of 3-6 cells "
    "in C_COLOR (from {5,6,7,9}, disjoint from "
    "A_COLOR's pool) at panel-local (c_top, "
    "c_left). The A→B edit pattern (which cells "
    "were added vs removed relative to A) is "
    "encoded by the difference. Rule (REPLAY THE "
    "A→B RELATIVE EDIT ONTO C, USING C'S COLOR "
    "FOR ADDS): COMPUTE the relative edit by "
    "differencing A and B within their 3×3 bbox: "
    "ADDED CELLS (in B but not in A) and REMOVED "
    "CELLS (in A but not in B). APPLY the same "
    "RELATIVE EDIT to C's 3×3 bbox: for each "
    "ADDED bbox position, PAINT C's "
    "corresponding bbox cell with C_COLOR; for "
    "each REMOVED bbox position, ERASE C's "
    "corresponding bbox cell to bg-0. Cells "
    "outside C's bbox stay unchanged. Net: C "
    "becomes C's original shape MODIFIED by the "
    "A→B edit pattern, with adds in C's color."
)

# Rivals: 'output A directly' refuted by ≥1 demo where output ≠ A
# (output is edited C). 'apply edit in A's color' refuted by ≥1 demo
# where adds use C's color, not A's. 'copy B into C verbatim' refuted
# by ≥1 demo where C's shape persists outside the edit cells.
# 'erase C entirely' refuted by any demo (C's unedited cells survive).
# 4 demos with varied A/B/C shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the input has three 5x5 panels separated by full color-8 columns",
    "panels A and B share a 3x3 edit bbox",
    "panel C has the same-size bbox at another position",
    "relative deletions clear C cells and relative additions use C's color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "no_panel_a", "identical_a_b")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5..5"},
    "grid_w":         {"type": "int", "default": "17", "valid": "17..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "variant":        {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "three_panels_with_separators",
                       "valid": "three_panels_with_separators"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_BBOX = 3  # 3×3 bbox for A/B edit and C target


def _rand_shape(rng, min_cells=3, max_cells=6):
    """Random 3×3 cell pattern with at least min_cells set."""
    while True:
        cells = set()
        for r in range(_BBOX):
            for c in range(_BBOX):
                if rng.random() < 0.5:
                    cells.add((r, c))
        if min_cells <= len(cells) <= max_cells:
            return cells


def _rand_edit(rng, a_cells, n_changes=2):
    """Make a B variant by flipping n_changes cells of A within bbox."""
    all_pos = [(r, c) for r in range(_BBOX) for c in range(_BBOX)]
    for _ in range(40):
        b_cells = set(a_cells)
        chosen = rng.sample(all_pos, min(n_changes, len(all_pos)))
        for p in chosen:
            if p in b_cells: b_cells.remove(p)
            else: b_cells.add(p)
        if b_cells != a_cells and 1 <= len(b_cells) <= 8:
            return b_cells
    return set(a_cells)


def _paint_cells(g, panel, top, left, cells, color, pw):
    base = panel * (pw + 1)
    for r, c in cells:
        g[top + r][base + left + c] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 2 full-height color-8 columns separating 3 equal-size panels."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    sep_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not sep_cols:
        return []  # degenerate no_separators — allowed
    errs = []
    if len(sep_cols) != 2:
        errs.append(f"expected 2 color-8 separator columns; found {len(sep_cols)}")
        return errs
    s1, s2 = sep_cols
    pw1, pw2, pw3 = s1, s2 - s1 - 1, w - s2 - 1
    if not (pw1 == pw2 == pw3):
        errs.append(f"panel widths unequal: {pw1}, {pw2}, {pw3}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_changes = 1; ph = ctx.draw_int("panel_h", 5, 5); pw = ctx.draw_int("panel_w", 5, 5)
    elif difficulty == "hard":
        n_changes = rng.randint(3, 4)
        ph = ctx.draw_int("panel_h", 5, 7); pw = ctx.draw_int("panel_w", 5, 7)
    else:
        n_changes = rng.randint(1, 3)
        ph = ctx.draw_int("panel_h", 4, 6); pw = ctx.draw_int("panel_w", 4, 6)
    a_color = rng.choice([1, 2, 3, 4])
    c_color = rng.choice([5, 6, 7, 9])

    w = 3 * pw + 2
    g = full_grid(ph, w, 0)
    for sep in (pw, 2 * pw + 1):
        for r in range(ph):
            g[r][sep] = 8
    a_cells = _rand_shape(rng, min_cells=3, max_cells=6)
    b_cells = _rand_edit(rng, a_cells, n_changes=n_changes)
    c_cells = _rand_shape(rng, min_cells=3, max_cells=6)
    # 3x3 edit bbox at a random panel-local position (fits since ph,pw >= 3).
    a_top = rng.randint(0, ph - _BBOX); a_left = rng.randint(0, pw - _BBOX)
    c_top = rng.randint(0, ph - _BBOX); c_left = rng.randint(0, pw - _BBOX)
    _paint_cells(g, 0, a_top, a_left, a_cells, a_color, pw)
    _paint_cells(g, 1, a_top, a_left, b_cells, a_color, pw)
    _paint_cells(g, 2, c_top, c_left, c_cells, c_color, pw)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 17, 0)
    _A_d = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)}
    _B_d = {(0, 0), (1, 1), (2, 1), (2, 2)}
    _C_d = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)}
    if name == "no_separators":
        _paint_cells(g, 0, 1, 1, _A_d, 4, 5)
        _paint_cells(g, 1, 1, 1, _B_d, 4, 5)
        _paint_cells(g, 2, 0, 2, _C_d, 6, 5)
        return g
    if name == "no_panel_a":
        for sep in (5, 11):
            for r in range(5):
                g[r][sep] = 8
        _paint_cells(g, 1, 1, 1, _B_d, 4, 5)
        _paint_cells(g, 2, 0, 2, _C_d, 6, 5)
        return g
    if name == "identical_a_b":
        for sep in (5, 11):
            for r in range(5):
                g[r][sep] = 8
        _paint_cells(g, 0, 1, 1, _A_d, 4, 5)
        _paint_cells(g, 1, 1, 1, _A_d, 4, 5)
        _paint_cells(g, 2, 0, 2, _C_d, 6, 5)
        return g
    return g
