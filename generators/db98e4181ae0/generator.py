"""Generator for arc_puzzle_bank_nineteenth21:H128 — 5-panel support-op analogy.

Rule (verified against canonical): the grid splits column-wise into 5 equal panels
separated by single 0-columns: a, b, result, c, d. The rule infers the boolean
support op (union / intersection / xor) such that op(a, b) == result, then outputs
op(c, d), recoloured to c/d's colour.

This generator builds proper 5-panel inputs:
  - a, b: random binary panels that OVERLAP partially (so union/intersection/xor
    are all distinct -> the inferred op is unambiguous);
  - result = op(a, b) for a chosen op;
  - c, d: random binary panels (so op(c, d) is non-trivial);
  - a/b/result in colour A, c/d in colour B.

Combinatorial axes: panel_h, panel_w, op, colours, panel densities.
Degenerates: no_separators, single_panel, empty_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db98e4181ae0"
VERSION = "3.0.3"  # panel_w capped at 5 (w=5pw+4 must fit 30; hard's pw=6 drew 34 wide)
TASK_ID = "db98e4181ae0"

SUMMARY = (
    "0-bg grid of 5 equal PANELS (each ph x pw) separated by single 0-columns: "
    "a, b, result, c, d. a/b/result are colour A; c/d are colour B. a and b "
    "overlap partially; result = OP(a,b) for OP in {union, intersection, xor} "
    "(unambiguous because all three differ). Rule: infer OP from a,b,result, then "
    "output OP(c,d) recoloured to colour B. Output is ph x pw."
)

INVARIANTS = [
    "background is 0",
    "5 equal-width panels separated by single 0-columns",
    "a and b overlap so union/intersection/xor are all distinct (unambiguous op)",
    "result panel equals op(a,b); output = op(c,d)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "single_panel", "empty_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "panel_w":        {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "op":             {"type": "str", "default": "rng",
                       "valid": "union|intersection|xor"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "five_panels", "valid": "five_panels"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "medium", "valid": "medium"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_OPS = ("union", "intersection", "xor")


def _rand_cells(rng, ph, pw, lo, hi):
    allp = [(r, c) for r in range(ph) for c in range(pw)]
    k = rng.randint(lo, min(hi, len(allp)))
    return set(rng.sample(allp, k))


def _apply(op, a, b):
    if op == "union":
        return a | b
    if op == "intersection":
        return a & b
    return a ^ b   # xor


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # ARC cap: 5 panels wide -> w = 5*pw+4 <= 30 -> pw <= 5 (the old hard
    # band's pw=6 emitted 34-wide grids; validity sweep)
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 3, 4); pw = ctx.draw_int("panel_w", 3, 4)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 5, 6); pw = ctx.draw_int("panel_w", 5, 5)
    else:
        ph = ctx.draw_int("panel_h", 3, 5); pw = ctx.draw_int("panel_w", 3, 5)
    rng = ctx.draw_rng("layout")
    op = overrides.get("op") if overrides.get("op") in _OPS else rng.choice(_OPS)
    col_ab, col_cd = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    ncell = ph * pw
    lo = max(1, ncell // 4); hi = max(lo, (ncell * 3) // 4)

    # a,b overlap partially so union/intersection/xor are all distinct (op unambiguous)
    a = b = set()
    for _ in range(80):
        a = _rand_cells(rng, ph, pw, lo, hi)
        b = _rand_cells(rng, ph, pw, lo, hi)
        if (a & b) and (a - b) and (b - a):
            break
    result = _apply(op, a, b)

    # c,d: ensure op(c,d) is non-empty AND not the whole panel. A full-panel result
    # becomes a large single-colour output, which is a weak/noisy training signal and trips
    # the generic all-solid-output defect lint.
    c = d = set()
    full = {(r, cc) for r in range(ph) for cc in range(pw)}
    for _ in range(200):
        c = _rand_cells(rng, ph, pw, lo, hi)
        d = _rand_cells(rng, ph, pw, lo, hi)
        q = _apply(op, c, d)
        if q and q != full:
            break

    w = 5 * pw + 4
    g = full_grid(ph, w, 0)
    panels = [(a, col_ab), (b, col_ab), (result, col_ab), (c, col_cd), (d, col_cd)]
    for i, (cells, color) in enumerate(panels):
        left = i * (pw + 1)
        for r, cc in cells:
            g[r][left + cc] = color
    return g



def _panel_cells(grid, left, pw):
    return {(r, c - left) for r, row in enumerate(grid)
            for c in range(left, left + pw) if row[c] != 0}


def _panel_colors(grid, left, pw):
    return {row[c] for row in grid for c in range(left, left + pw) if row[c] != 0}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the 5-panel a,b,result,c,d structure and its unambiguous op."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if (w - 4) % 5 != 0:
        return [f"width {w} is not 5 panels plus 4 separators"]
    pw = (w - 4) // 5
    if pw <= 0:
        return ["panel width must be positive"]
    seps = [pw + i * (pw + 1) for i in range(4)]
    for c in seps:
        if any(grid[r][c] != 0 for r in range(h)):
            errs.append(f"separator column {c} is not all background")
    lefts = [i * (pw + 1) for i in range(5)]
    cells = [_panel_cells(grid, left, pw) for left in lefts]
    if any(not c for c in cells):
        errs.append("all five panels must be non-empty")
    colors = [_panel_colors(grid, left, pw) for left in lefts]
    if any(len(cs) > 1 for cs in colors):
        errs.append("each panel must use at most one foreground color")
    if colors[0] != colors[1] or colors[1] != colors[2]:
        errs.append("a/b/result panels must share the same foreground color")
    if colors[3] != colors[4]:
        errs.append("c/d panels must share the same foreground color")
    if colors[0] and colors[3] and colors[0] == colors[3]:
        errs.append("support panels and query panels should use distinct colors")
    a, b, result, c, d = cells
    matches = [op for op in _OPS if _apply(op, a, b) == result]
    if len(matches) != 1:
        errs.append(f"a,b,result do not identify a unique op (matches={matches})")
    else:
        q = _apply(matches[0], c, d)
        full = {(r, cc) for r in range(h) for cc in range(pw)}
        if not q:
            errs.append("query c,d would produce an empty output")
        elif q == full:
            errs.append("query c,d would produce a solid full-panel output")
    return errs

def _draw_from_degenerate(name, rng):
    ph, pw = 3, 3
    w = 5 * pw + 4
    g = full_grid(ph, w, 0)
    if name == "no_separators":
        # panels touching (no 0-columns) -> cannot split into 5
        for i in range(5):
            g[0][i * pw] = 1
            g[1][i * pw] = 1
        return g
    if name == "single_panel":
        # only one panel of content -> no a/b/result/c/d structure
        g[0][0] = 1; g[1][1] = 1
        return g
    if name == "empty_panels":
        # all-zero -> no op to infer
        return g
    return g
