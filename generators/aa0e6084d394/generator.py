"""Generator for 23581191.

Rule: for each (r,c,v), all cells in row r and col c get v. Where two
crosses overlap, cell becomes 2.

Combinatorial axes (8): grid_h/w, n_cells, palette_size, palette_kind,
position_bias, cell_layout, separation_kind, anchor_corner.
Degenerates: same_row, same_col, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa0e6084d394"
VERSION = "2.1.0"  # default path now guarantees >=2 distinct-row/col/color seeds so conflict markers are visible
TASK_ID = "aa0e6084d394"
SUMMARY = (
    "0-bg grid (h~7-14, w~8-16) with 1-3 ISOLATED non-bg "
    "cells, each in a distinct color (no color-2 in "
    "input). Cells are placed at distinct rows AND "
    "distinct columns. Rule: for each non-bg cell at "
    "(r, c) with color v, PAINT a full CROSS — every "
    "cell in row r and every cell in column c — with "
    "color v. Where TWO CROSSES OVERLAP (a cell sits "
    "on row(a) ∩ col(b) or row(b) ∩ col(a) for two "
    "different seeds), PAINT that intersection cell "
    "with color 2 (red) — the conflict marker — "
    "OVERRIDING the per-seed color. The original "
    "seed cells stay their own color. Net: input has "
    "isolated colored dots; output has full cross "
    "shapes per dot with red marking where two crosses "
    "cross-intersect."
)

INVARIANTS = [
    "background is 0",
    ">=1 non-bg cell",
    "if >=2 cells: distinct rows AND distinct cols",
    "no color 2 in input (rule writes 2 for output)",
]

CELL_LAYOUTS = ("scattered", "diagonal", "anti_diag", "corners", "spread")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("same_row", "same_col", "no_cells")
HELPFUL_TEXTURES = CELL_LAYOUTS

AXES = {'grid_h': {'type': 'int', 'default': 'rng 7..14', 'valid': '5..18'},
 'grid_w': {'type': 'int', 'default': 'rng 8..16', 'valid': '6..20'},
 'n_cells': {'type': 'int', 'default': 'rng 1..3', 'valid': '1..5'},
 'palette_size': {'type': 'int', 'default': '= n_cells', 'valid': '1..7'},
 'palette_kind': {'type': 'str', 'default': 'rng helpful', 'valid': 'warm|cool|broad|small'},
 'cell_layout': {'type': 'str',
                 'default': 'rng helpful',
                 'valid': 'scattered|diagonal|anti_diag|corners|spread'},
 'position_bias': {'type': 'str',
                   'default': 'rng spread|center|edge',
                   'valid': 'spread|center|edge'},
 'anchor_corner': {'type': 'bool', 'default': 'false', 'valid': 'true|false'},
 'texture': {'type': 'str',
             'default': 'alias for cell_layout',
             'valid': 'scattered|diagonal|anti_diag|corners|spread|same_row|same_col|no_cells'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 8
    elif difficulty == "hard":
        h_lo, h_hi = 12, 18
    else:
        h_lo, h_hi = 7, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n = int(overrides.get("n_cells", ctx.draw_int("n_cells", 2, 3)))
    n = max(2, min(min(h, w), n))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7, 8]
    elif palette_kind == "small":
        pool = [1, 3]
    else:
        pool = [1, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    palette = pool[:n]
    if len(palette) < n:
        for c in [1, 3, 4, 5, 6, 7, 8, 9]:
            if c not in palette:
                palette.append(c)
            if len(palette) == n:
                break
    layout = (overrides.get("texture") or overrides.get("cell_layout")
              or ctx.draw_choice("cell_layout", list(CELL_LAYOUTS)))
    rs, cs = _layout_positions(layout, h, w, n, rng)
    g = full_grid(h, w, 0)
    for i in range(n):
        g[rs[i]][cs[i]] = palette[i]
    return g


def _layout_positions(layout, h, w, n, rng):
    if layout == "diagonal":
        rs = list(range(min(n, h)))
        cs = list(range(min(n, w)))
        return rs, cs
    if layout == "anti_diag":
        rs = list(range(min(n, h)))
        cs = [w - 1 - i for i in range(min(n, w))]
        return rs, cs
    if layout == "corners":
        # Corners alone reuse rows/columns when n>=2, hiding the conflict-marker
        # rule behind an illegal same-row/same-col default.  Keep the corner bias
        # but insert a center witness for the third seed so rows/cols stay unique.
        pts = [(0, 0), (h - 1, w - 1)]
        if n >= 3:
            pts.append((h // 2, w // 2))
        return [r for r, _ in pts[:n]], [c for _, c in pts[:n]]
    if layout == "spread":
        step_r = max(1, h // (n + 1))
        step_c = max(1, w // (n + 1))
        rs = [step_r * (i + 1) for i in range(n) if step_r * (i + 1) < h]
        cs = [step_c * (i + 1) for i in range(n) if step_c * (i + 1) < w]
        while len(rs) < n: rs.append(rs[-1] if rs else 0)
        while len(cs) < n: cs.append(cs[-1] if cs else 0)
        return rs, cs
    rs = rng.sample(range(h), min(n, h))
    cs = rng.sample(range(w), min(n, w))
    while len(rs) < n: rs.append(rs[-1])
    while len(cs) < n: cs.append(cs[-1])
    return rs, cs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color1 = rng.choice([1, 3, 4, 5, 6, 7, 8, 9])
    color2 = rng.choice([c for c in [1, 3, 4, 5, 6, 7, 8, 9]
                         if c != color1])
    if name == "same_row":
        r = h // 2
        g[r][1] = color1
        g[r][w - 2] = color2
        return g
    if name == "same_col":
        c = w // 2
        g[1][c] = color1
        g[h - 2][c] = color2
        return g
    if name == "no_cells":
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if len(cells) < 2:
        errs.append("expected at least two seed cells so red conflict intersections are visible")
    if any(v == 2 for _, _, v in cells):
        errs.append("input may not contain color 2; the rule reserves it for conflict markers")
    rows = [r for r, _, _ in cells]
    cols = [c for _, c, _ in cells]
    colors = [v for _, _, v in cells]
    if len(rows) != len(set(rows)):
        errs.append("seed rows must be distinct")
    if len(cols) != len(set(cols)):
        errs.append("seed columns must be distinct")
    if len(colors) != len(set(colors)):
        errs.append("seed colors must be distinct")
    return errs
