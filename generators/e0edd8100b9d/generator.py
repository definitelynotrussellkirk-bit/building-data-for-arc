"""Generator for arc_puzzle_bank_twentieth21:H134.

Three 4x4 panels show A, transformed-and-recolored B, and a query C. The
canonical rule infers both the transform and color map from A to B.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers (no color-8 separator columns → rule
cannot identify panels); identity_transform (panel B == panel A
nonzero-support → t = identity); identity_recolor (target colors ==
source colors → no recolor).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e0edd8100b9d"
VERSION = "3.1.0"  # FIXED 4x14 grid + FIXED A/C patterns (only transform+colors varied) -> shape-locked-in/out. Rule splits 3 square panels (panel-w=(cols-2)/3) and infers transform+recolor from A->B. Now vary panel size n (3-5) and randomize asymmetric A/C patterns."
TASK_ID = "e0edd8100b9d"
SUMMARY = (
    "Three square panels of size n∈{3,4,5} separated by full color-8 "
    "divider columns. Panel A is a random asymmetric 3-color support; panel "
    "B is a visible transform of A with a consistent recolor; panel C uses "
    "only A's source colors. Rule: infer the transform and recolor from "
    "A→B, then apply both to C and emit the transformed/recolored query panel."
)

INVARIANTS = [
    "the input has three n×n panels (n in 3..5) separated by full color-8 columns",
    "panel B is a nonzero-support transform of panel A with a consistent recolor",
    "panel C uses only colors seen in panel A",
    "the inferred transform/recolor are visible (not pure identity evidence)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "identity_transform", "identity_recolor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "transform":         {"type": "enum", "default": "rng", "valid": "r1|r2|r3|fh|fv|tr|atr"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "position_bias":     {"type": "str", "default": "three_4x4_panels",
                          "valid": "three_4x4_panels"},
    "n_distinct_colors": {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CODES = ["r1", "r2", "r3", "fh", "fv", "tr", "atr"]
_A = [(0, 0, 1), (1, 0, 1), (1, 1, 2), (2, 1, 2), (2, 2, 3)]
_C = [(0, 1, 1), (0, 2, 2), (1, 1, 2), (2, 0, 3)]


def _grid_from_cells(cells, colors, n=4):
    out = full_grid(n, n, 0)
    for r, c, slot in cells:
        out[r][c] = colors[slot - 1]
    return out


def _support(grid):
    return frozenset((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v)


def _rand_pattern(rng, n, klo, khi):
    """Random subset of n×n cells (>=3 cells) with all 3 color slots used."""
    cells_pos = [(r, c) for r in range(n) for c in range(n)]
    k = rng.randint(max(3, klo), min(khi, n * n - 1))
    chosen = rng.sample(cells_pos, k)
    out = []
    for i, (r, c) in enumerate(chosen):
        slot = (i % 3) + 1 if i < 3 else rng.randint(1, 3)
        out.append((r, c, slot))
    return out


def _xform_grid(grid, code):
    h = len(grid)
    w = len(grid[0])
    if code == "r1":
        return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == "r2":
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if code == "r3":
        return [[grid[r][w - 1 - c] for r in range(h)] for c in range(w - 1, -1, -1)]
    if code == "fh":
        return [list(reversed(row)) for row in grid]
    if code == "fv":
        return list(reversed([row[:] for row in grid]))
    if code == "tr":
        return [[grid[r][c] for r in range(h)] for c in range(w)]
    return [[grid[h - 1 - r][w - 1 - c] for r in range(h - 1, -1, -1)] for c in range(w - 1, -1, -1)]


def _recolor(grid, mapping):
    return [[mapping.get(v, v) for v in row] for row in grid]


def _paste_panel(out, panel, grid, n):
    left = panel * (n + 1)
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
        codes = ["fh", "fv", "tr"]; n = ctx.draw_int("panel_n", 3, 4)
    elif difficulty == "hard":
        codes = _CODES; n = ctx.draw_int("panel_n", 4, 5)
    else:
        codes = _CODES; n = ctx.draw_int("panel_n", 3, 5)
    code = ctx.draw_choice("transform", codes)
    source_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    target_colors = rng.sample([c for c in [1, 2, 3, 4, 5, 6, 7, 9]], 3)
    while target_colors == source_colors:                 # ensure recolor visible
        target_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    mapping = dict(zip(source_colors, target_colors))

    for _attempt in range(40):
        a_cells = _rand_pattern(rng, n, 4, n * n - 1)
        a = _grid_from_cells(a_cells, source_colors, n)
        xa = _xform_grid(a, code)
        if _support(xa) == _support(a):                   # transform must be visible
            continue
        b = _recolor(xa, mapping)
        c = _grid_from_cells(_rand_pattern(rng, n, 3, n * n - 1), source_colors, n)
        w = 3 * n + 2
        g = full_grid(n, w, 0)
        for sep in (n, 2 * n + 1):
            for r in range(n):
                g[r][sep] = 8
        _paste_panel(g, 0, a, n)
        _paste_panel(g, 1, b, n)
        _paste_panel(g, 2, c, n)
        return g
    # fallback: the original fixed 4x4 layout
    a = _grid_from_cells(_A, source_colors, 4)
    b = _recolor(_xform_grid(a, "fh"), mapping)
    c = _grid_from_cells(_C, source_colors, 4)
    g = full_grid(4, 14, 0)
    for sep in (4, 9):
        for r in range(4):
            g[r][sep] = 8
    _paste_panel(g, 0, a, 4); _paste_panel(g, 1, b, 4); _paste_panel(g, 2, c, 4)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(4, 14, 0)
    if name == "no_dividers":
        # No color-8 separators — rule cannot identify panels.
        for r, c, _slot in _A:
            g[r][c] = 4 + (_slot - 1)
        return g
    if name == "identity_transform":
        # Panel B == panel A.
        for sep in (4, 9):
            for r in range(4):
                g[r][sep] = 8
        for r, c, slot in _A:
            color = 4 + (slot - 1)
            g[r][c] = color
            g[r][5 + c] = color
        for r, c, slot in _C:
            g[r][10 + c] = 4 + (slot - 1)
        return g
    if name == "identity_recolor":
        # Source == target colors — no recolor.
        for sep in (4, 9):
            for r in range(4):
                g[r][sep] = 8
        for r, c, slot in _A:
            color = 4 + (slot - 1)
            g[r][c] = color
            g[r][5 + c] = color
        for r, c, slot in _C:
            g[r][10 + c] = 4 + (slot - 1)
        return g
    return g



def _split_panels_for_check(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    if h <= 0 or (w - 2) % 3 != 0:
        return None
    n = (w - 2) // 3
    if h != n or not (3 <= n <= 5):
        return None
    if any(grid[r][n] != 8 or grid[r][2 * n + 1] != 8 for r in range(n)):
        return None
    panels = []
    for left in (0, n + 1, 2 * n + 2):
        panels.append([row[left:left + n] for row in grid])
    return n, panels


def self_check(grid, *, difficulty=None, meta=None):
    """Three square panels, full dividers, visible A→B transform/recolor evidence."""
    errs = []
    split = _split_panels_for_check(grid)
    if split is None:
        return ["expected three n×n panels with full color-8 divider columns"]
    n, (a, b, c) = split
    source = {v for row in a for v in row if v not in {0, 8}}
    target = {v for row in b for v in row if v not in {0, 8}}
    query = {v for row in c for v in row if v not in {0, 8}}
    if len(source) < 3:
        errs.append(f"panel A should expose at least 3 source colors, got {sorted(source)}")
    if len(target) < 3:
        errs.append(f"panel B should expose at least 3 target colors, got {sorted(target)}")
    if not query:
        errs.append("panel C is empty")
    if query and not query <= source:
        errs.append(f"panel C has colors outside panel A: {sorted(query - source)}")
    if _support(a) == _support(b):
        errs.append("panel B support equals panel A support; transform evidence is hidden")
    if source == target:
        errs.append("target colors equal source colors; recolor evidence is hidden")
    return errs
