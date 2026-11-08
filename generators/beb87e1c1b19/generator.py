"""Generator for arc_puzzle_bank_twentysecond21:H154 — 3-panel support transform.

Rule: Three 3x3 panels separated by full color-8 columns. Panel B has
the same support as transformed panel A; output overlays panel C with
its own transformed copy (nonzero transformed cells overwrite bg in C).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: identity_transform (A==B → 8 valid ops fix A,
transform inference is non-canonical), empty_query (panel C all bg →
overlay has nothing to do), single_cell_panel (panel A has 1 cell →
many transforms produce identical B, ambiguous inference).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "beb87e1c1b19"
VERSION = "2.3.0"  # fix all_background: the output is c overlaid with transform(c) (both c_color); when c's support UNION its transform covers all 9 cells the output is solid c_color. Redraw C so the union always leaves >=1 empty cell (output keeps both c_color and 0)."
TASK_ID = "beb87e1c1b19"

SUMMARY = (
    "FIXED 3×11 grid with: "
    "(a) THREE 3×3 PANELS "
    "separated by FULL-"
    "HEIGHT COLOR-8 (cyan) "
    "DIVIDER COLUMNS at "
    "cols 3 and 7. "
    "Panels A (cols 0-2), "
    "B (cols 4-6), C "
    "(cols 8-10). PANEL "
    "A is a fixed L-"
    "shape (cells (0,0), "
    "(1,0), (1,1)) "
    "recolored in random "
    "non-{0, 8} A-COLOR. "
    "PANEL B is the same "
    "L-shape transformed "
    "by a chosen "
    "transform CODE "
    "(r1=rot90CW, r2=180, "
    "r3=CCW, fh=flip LR, "
    "fv=flip UD, tr=transpose"
    ", atr=anti-transpose) "
    "recolored in B-COLOR. "
    "PANEL C is a "
    "different fixed shape "
    "(cells (0,2), (1,1), "
    "(1,2)) recolored in "
    "C-COLOR. Rule (INFER "
    "TRANSFORM FROM A→B, "
    "APPLY TO C, UNION "
    "WITH ORIGINAL C): "
    "compare the support "
    "(cell positions) of "
    "PANEL A and PANEL B "
    "— infer which "
    "dihedral transform T "
    "maps A's support to "
    "B's. APPLY T to "
    "PANEL C's support. "
    "OVERLAY the "
    "transformed C cells "
    "(painted in C's "
    "color) onto the "
    "original C panel — "
    "nonzero transformed "
    "cells overwrite bg "
    "in C. Net: C panel "
    "gets enriched with "
    "T-transformed copies "
    "of itself. Flag: "
    "INTRINSIC-LOW "
    "DIVERSITY — fixed "
    "shapes × 7 transforms "
    "× small color set → "
    "~19 distinct outputs."
)

INVARIANTS = [
    "the input has three 3x3 panels separated by full color-8 columns",
    "panel B has the same support as transformed panel A",
    "panel C is overlaid with its own transformed copy",
    "nonzero transformed C cells overwrite background in the original C panel",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_transform", "empty_query", "single_cell_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "transform":      {"type": "enum", "default": "rng",
                       "valid": "r1|r2|r3|fh|fv|tr|atr"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "three_3x3_panels_with_separators",
                       "valid": "three_3x3_panels_with_separators"},
    "n_distinct_colors": {"type": "int", "default": "3..4", "valid": "2..6"},
    "density":        {"type": "str", "default": "fixed_3panel", "valid": "fixed_3panel"},
    "grid_h":         {"type": "int", "default": "3", "valid": "3..3"},
    "grid_w":         {"type": "int", "default": "11", "valid": "11..11"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CODES = ["r1", "r2", "r3", "fh", "fv", "tr", "atr"]
_A = [
    [1, 0, 0],
    [1, 1, 0],
    [0, 0, 0],
]
_C = [
    [0, 0, 5],
    [0, 5, 5],
    [0, 0, 0],
]


def _xform_grid(grid, code):
    h = len(grid)
    w = len(grid[0])
    if code == "r1":       # rotate 90 degrees clockwise
        return [[grid[h - 1 - c][r] for c in range(h)] for r in range(w)]
    if code == "r2":       # rotate 180 degrees
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if code == "r3":       # rotate 90 degrees counter-clockwise
        return [[grid[c][w - 1 - r] for c in range(h)] for r in range(w)]
    if code == "fh":       # mirror left/right
        return [list(reversed(row)) for row in grid]
    if code == "fv":       # mirror up/down
        return [row[:] for row in reversed(grid)]
    if code == "tr":       # transpose across the main diagonal
        return [[grid[c][r] for c in range(h)] for r in range(w)]
    if code == "atr":      # transpose across the anti-diagonal
        return [[grid[h - 1 - c][w - 1 - r] for c in range(h)] for r in range(w)]
    raise ValueError(f"unknown transform code: {code}")


def _rand_support(rng, lo, hi):
    """Random 3x3 0/1 support with lo..hi filled cells."""
    k = rng.randint(lo, hi)
    cells = rng.sample([(r, c) for r in range(3) for c in range(3)], k)
    g = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for r, c in cells:
        g[r][c] = 1
    return g


def _rand_asym_support(rng):
    """Random 3x3 support whose 8 dihedral images are all distinct, so the
    A->B transform is uniquely inferable (matches the rule's assumption)."""
    for _ in range(80):
        g = _rand_support(rng, 2, 5)
        imgs = {tuple(map(tuple, g))}
        for code in _CODES:
            imgs.add(tuple(map(tuple, _xform_grid(g, code))))
        if len(imgs) == 8:                    # id + 7 codes all distinct
            return g
    return [[1, 1, 0], [0, 1, 0], [1, 0, 0]]  # fallback with full dihedral orbit


def _recolor(grid, color):
    return [[color if v else 0 for v in row] for row in grid]


def _paste_panel(out, panel, grid):
    left = panel * 4
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            out[r][left + c] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        code = ctx.draw_choice("transform", ["fh", "fv", "tr"])
    elif difficulty == "hard":
        code = ctx.draw_choice("transform", _CODES)
    else:
        code = ctx.draw_choice("transform", _CODES)
    a_color = rng.choice([1, 2, 3, 4])
    b_color = rng.choice([2, 3, 4, 6])
    c_color = rng.choice([5, 6, 7, 9])
    # v2.0.0 used FIXED L-shapes for A and C -> only colors varied (distinct 19).
    # A must be dihedral-asymmetric so the A->B transform is uniquely inferable;
    # C can be any non-empty support. Random supports -> far more outputs.
    a_grid = _rand_asym_support(rng)
    # Output is c overlaid with transform(c). When c's support UNION its
    # transform covers all 9 cells the whole 3x3 becomes one colour (solid).
    # Redraw C until the union leaves at least one empty cell.
    c_grid = _rand_support(rng, 2, 6)
    for _ in range(80):
        tc = _xform_grid(c_grid, code)
        if any(not (c_grid[r][col] or tc[r][col])
               for r in range(3) for col in range(3)):
            break
        c_grid = _rand_support(rng, 2, 6)
    a = _recolor(a_grid, a_color)
    b = _recolor(_xform_grid(a_grid, code), b_color)
    c = _recolor(c_grid, c_color)

    g = full_grid(3, 11, 0)
    for sep in (3, 7):
        for r in range(3):
            g[r][sep] = 8
    for idx, panel in enumerate([a, b, c]):
        _paste_panel(g, idx, panel)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(3, 11, 0)
    for sep in (3, 7):
        for r in range(3):
            g[r][sep] = 8
    if name == "identity_transform":
        # A and B identical — many transforms map A→A, rule's
        # "infer one transform" branch picks ambiguously.
        a = _recolor(_A, 1)
        c = _recolor(_C, 5)
        for idx, panel in enumerate([a, a, c]):
            _paste_panel(g, idx, panel)
        return g
    if name == "empty_query":
        # Panel C is empty — the "overlay with transformed copy"
        # has no content to overlay; output equals an empty C.
        a = _recolor(_A, 1)
        b = _recolor(_xform_grid(_A, "fh"), 3)
        empty = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for idx, panel in enumerate([a, b, empty]):
            _paste_panel(g, idx, panel)
        return g
    if name == "single_cell_panel":
        # Panel A has just one cell — every rotation/flip maps A→A,
        # transform inference can't distinguish ops.
        a = [[0, 1, 0], [0, 0, 0], [0, 0, 0]]
        b = [[0, 1, 0], [0, 0, 0], [0, 0, 0]]
        c = _recolor(_C, 5)
        for idx, panel in enumerate([a, b, c]):
            _paste_panel(g, idx, panel)
        return g
    return g



def _support(panel):
    return [[1 if value != 0 else 0 for value in row] for row in panel]


def _panel(grid, idx):
    left = idx * 4
    return [[grid[r][left + c] for c in range(3)] for r in range(3)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if len(grid) != 3 or any(len(row) != 11 for row in grid):
        return ["grid must be exactly 3x11"]
    if any(grid[r][3] != 8 or grid[r][7] != 8 for r in range(3)):
        errors.append("divider columns 3 and 7 must be solid color 8")
    panels = [_panel(grid, i) for i in range(3)]
    for idx, panel in enumerate(panels):
        if any(8 in row for row in panel):
            errors.append(f"panel {idx} contains divider color 8")
    a, b, c = map(_support, panels)
    matches = [code for code in _CODES if _xform_grid(a, code) == b]
    if len(matches) != 1:
        errors.append(f"A->B transform must be unique, got {matches}")
    if sum(sum(row) for row in c) < 2:
        errors.append("query panel C should have at least two support cells")
    return sorted(set(errors))
