"""Generator for arc_additional_puzzles_21_set9:H60.

Three panels are separated by full color-5 columns. The first two panels show
a translation vector, and the rule applies that vector to the third panel.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_separators, no_object, identical_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "adf40dc220b5"
VERSION = "2.1.0"  # oversize fix: clamp pw so 3-panel grid fits 30 cols (hard pw=11 -> w=35 -> clipped/corrupt)
TASK_ID = "adf40dc220b5"
SUMMARY = (
    "Grid is split into 3 panels by 2 full color-5 separator columns. "
    "Each panel holds exactly one connected non-bg shape. Panels A "
    "(left) and B (middle) share the SAME shape and color; the shape's "
    "position differs — the translation vector (dr, dc) = bbox_top_left(B) "
    "- bbox_top_left(A) is the rule's only learned quantity. Panel C "
    "(right) has a (possibly different-colored) shape. Rule output is a "
    "C-panel-sized grid containing C's shape translated by (dr, dc); "
    "cells that would translate outside C's panel are silently dropped."
)

# Rivals: 'output is input' refuted by demos (output is panel-sized).
# 'output is panel C verbatim' refuted by demos where the translation
# is nonzero (so C shifts). 'use A's color in output' refuted by demos
# with C-color ≠ A-color. 'translate by (1,1) always' refuted by
# demos with varied vectors. 'reflect, not translate' refuted by
# demos where translation differs from any reflection. 4 demos
# covering 4 different (dr, dc) signs (++/+-/-+/-) pin the vector.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "two full color-5 separator columns create three panels",
    "each panel contains exactly one connected non-bg component",
    "panels A and B share the same shape AND same color (the demo)",
    "panel C's translation by (dr, dc) keeps at least one cell in-bounds",
    "translation vector (dr, dc) is non-zero (so the rule's effect is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "no_object", "identical_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "delta":          {"type": "choice", "default": "rng",
                       "valid": "small row/column translations"},
    "shape":          {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "three_panels_5col",
                       "valid": "three_panels_5col"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_separators|no_object|identical_panels"},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],                # S-tetromino
    [(0, 1), (1, 0), (1, 1), (1, 2)],                # T-tetromino
    [(0, 0), (0, 1), (1, 1), (2, 1)],                # L-down
    [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],        # zigzag-5
    [(0, 0), (0, 1)],                                # H-domino
    [(0, 0), (1, 0)],                                # V-domino
    [(0, 0), (0, 1), (1, 0)],                        # L-tromino
    [(0, 0), (1, 0), (1, 1), (1, 2)],                # T-down
    [(0, 0), (0, 1), (0, 2), (1, 1)],                # T-up
    [(0, 0), (1, 0), (2, 0), (2, 1)],                # L-tetromino
]
_DELTAS = [(1, 1), (1, 2), (2, 1), (-1, 2), (2, -1),
           (-1, 1), (1, -1), (-2, 1), (2, 2), (-1, -2),
           (-2, -1), (3, 1), (1, 3)]


def _paint(g, panel_left, top, left, cells, color):
    for r, c in cells:
        g[top + r][panel_left + left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # Canonical examples are tiny 4-row, 14/17-col three-panel demos.
    # Keep the same visual family instead of training on oversized galleries.
    canon_shapes = _SHAPES[:5]
    cells_ab = canon_shapes[ctx.draw_int("shape_ab", 0, len(canon_shapes) - 1)]
    cells_c = canon_shapes[ctx.draw_int("shape_c", 0, len(canon_shapes) - 1)]
    if difficulty == "hard":
        ph_lo, ph_hi, pw_lo, pw_hi = 4, 5, 4, 5
    else:
        ph_lo, ph_hi, pw_lo, pw_hi = 4, 4, 4, 5
    ph = ctx.draw_int("panel_h", ph_lo, ph_hi)
    pw = ctx.draw_int("panel_w", pw_lo, pw_hi)
    pw = min(pw, (30 - 2) // 3)   # 3 panels + 2 separators must fit 30 cols (hard pw=11 -> w=35 -> clipped/corrupt)
    h, w = ph, pw * 3 + 2
    g = full_grid(h, w, 0)
    sep1, sep2 = pw, pw * 2 + 1
    for r in range(h):
        g[r][sep1] = 5
        g[r][sep2] = 5

    mh_ab = max(r for r, _c in cells_ab) + 1
    mw_ab = max(c for _r, c in cells_ab) + 1
    mh_c = max(r for r, _c in cells_c) + 1
    mw_c = max(c for _r, c in cells_c) + 1

    # Sample a delta that keeps shape A's translated copy in-bounds in
    # panel B AND keeps shape C's translated copy with ≥1 cell in
    # panel C.
    placement = None
    for _ in range(80):
        dr, dc = rng.choice(_DELTAS)
        # A position
        a_top_lo = max(0, -dr)
        a_top_hi = ph - mh_ab - max(0, dr)
        a_left_lo = max(0, -dc)
        a_left_hi = pw - mw_ab - max(0, dc)
        if a_top_hi < a_top_lo or a_left_hi < a_left_lo:
            continue
        top_a = rng.randint(a_top_lo, a_top_hi)
        left_a = rng.randint(a_left_lo, a_left_hi)
        # C position — only require ≥1 translated cell stays in-bounds
        c_top_lo = 0
        c_top_hi = ph - mh_c
        c_left_lo = 0
        c_left_hi = pw - mw_c
        if c_top_hi < c_top_lo or c_left_hi < c_left_lo:
            continue
        top_c = rng.randint(c_top_lo, c_top_hi)
        left_c = rng.randint(c_left_lo, c_left_hi)
        # Check at least one C cell stays in-bounds after translation
        translated_in_bounds = [(top_c + r + dr, left_c + c + dc)
                                for r, c in cells_c
                                if 0 <= top_c + r + dr < ph
                                and 0 <= left_c + c + dc < pw]
        if not translated_in_bounds:
            continue
        placement = (dr, dc, top_a, left_a, top_c, left_c)
        break

    if placement is None:
        # Deterministic compact fallback that is known to fit the canonical
        # 4x4 panel case for every shape in canon_shapes.
        cells_ab = [(0, 0), (1, 0), (1, 1)]
        cells_c = [(0, 0), (1, 0), (1, 1)]
        mh_ab = mw_ab = mh_c = mw_c = 2
        dr, dc = 1, 1
        top_a, left_a = 0, 0
        top_c, left_c = 0, 0
    else:
        dr, dc, top_a, left_a, top_c, left_c = placement

    color_ab = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    color_c = rng.choice([c for c in [1, 2, 3, 4, 6, 7, 8, 9] if c != color_ab])
    _paint(g, 0, top_a, left_a, cells_ab, color_ab)
    _paint(g, sep1 + 1, top_a + dr, left_a + dc, cells_ab, color_ab)
    _paint(g, sep2 + 1, top_c, left_c, cells_c, color_c)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify compact three-panel translation-demo invariants."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h not in (4, 5):
        errs.append(f"expected compact canonical height 4 or 5, got {h}")
    div_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(div_cols) != 2:
        errs.append(f"found {len(div_cols)} full-height color-5 column(s), expected exactly 2")
        return errs
    sep1, sep2 = div_cols
    panels = [(0, sep1), (sep1 + 1, sep2), (sep2 + 1, w)]
    widths = [b - a for a, b in panels]
    if min(widths) < 4 or max(widths) > 5:
        errs.append(f"expected compact panel widths 4..5, got {widths}")

    def comps(panel):
        left, right = panel
        seen = set()
        out = []
        for r in range(h):
            for c in range(left, right):
                v = grid[r][c]
                if v == 0 or v == 5 or (r, c) in seen:
                    continue
                q = [(r, c)]
                seen.add((r, c))
                cells = []
                while q:
                    rr, cc = q.pop()
                    cells.append((rr, cc - left, grid[rr][cc]))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < h and left <= nc < right and (nr, nc) not in seen and grid[nr][nc] == v:
                            seen.add((nr, nc)); q.append((nr, nc))
                out.append(cells)
        return out

    cs = [comps(p) for p in panels]
    if any(len(x) != 1 for x in cs):
        errs.append(f"expected exactly one non-bg component per panel, got {[len(x) for x in cs]}")
        return errs
    a, b, c = [x[0] for x in cs]
    def norm_shape(cells):
        rs = [r for r, _c, _v in cells]; cs_ = [c for _r, c, _v in cells]
        r0, c0 = min(rs), min(cs_)
        return sorted((r - r0, cc - c0) for r, cc, _v in cells)
    def top_left(cells):
        return min(r for r, _c, _v in cells), min(c for _r, c, _v in cells)
    if norm_shape(a) != norm_shape(b):
        errs.append("panels A and B must contain the same shape")
    if {v for _r, _c, v in a} != {v for _r, _c, v in b}:
        errs.append("panels A and B must share the same color")
    dr, dc = top_left(b)[0] - top_left(a)[0], top_left(b)[1] - top_left(a)[1]
    if dr == 0 and dc == 0:
        errs.append("translation vector is zero/hidden")
    # C translated by the demo vector must leave at least one visible output cell.
    cw = widths[2]
    if not any(0 <= r + dr < h and 0 <= cc + dc < cw for r, cc, _v in c):
        errs.append("panel C would translate entirely out of bounds")
    return errs

def _draw_from_degenerate(name, rng):
    ph, pw = 9, 7
    h, w = ph, pw * 3 + 2
    g = full_grid(h, w, 0)
    sep1, sep2 = pw, pw * 2 + 1
    if name == "no_separators":
        # Three components but no 5-cols — rule's "3 panels"
        # split fails; vector inference undefined.
        for r, c in [(2, 1), (3, 1), (3, 2)]: g[r][c] = 4
        for r, c in [(3, 9), (4, 9), (4, 10)]: g[r][c] = 4
        for r, c in [(2, 17), (3, 17), (3, 18)]: g[r][c] = 4
        return g
    for r in range(h):
        g[r][sep1] = 5
        g[r][sep2] = 5
    if name == "no_object":
        # Separators present but query panel empty — rule has
        # nothing to translate.
        for r, c in [(2, 1), (3, 1), (3, 2)]: g[r][c] = 4
        for r, c in [(3, 9), (4, 9), (4, 10)]: g[r][c] = 4
        return g
    if name == "identical_panels":
        # Panels A and B identical (delta = 0,0) — rule's translate
        # vector collapses to identity; effect invisible on panel C.
        for r, c in [(2, 1), (3, 1), (3, 2)]: g[r][c] = 4
        for r, c in [(2, 9), (3, 9), (3, 10)]: g[r][c] = 4
        for r, c in [(2, 17), (3, 17), (3, 18)]: g[r][c] = 4
        return g
    return g
