"""Generator for arc_puzzle_bank_twentysecond21:H148.

Three N×N panels show A, transformed-recolored B, and a query C; the rule
infers transform + color-map from A→B and applies both to C. Output is N×N.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers (no color-8 separator columns → rule
cannot identify panels); identity_transform (panel B == panel A
→ t = identity); identity_recolor (target == source colors → no
recolor mapping).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3277b7c6f8f6"
VERSION = "3.1.0"  # shape-locked-in/out (fixed 3x3 panels -> 3x11 in, 3x3 out): 3 panels a|b|c, b=transform+recolor of a, rule deduces a->b transform and applies to c (output N x N). Now panel size N=3..5 + random a/c panels.
TASK_ID = "3277b7c6f8f6"
SUMMARY = (
    "Input = three N×N PANELS (N=3..5) separated by full color-8 divider "
    "columns. Panel A is a random N×N pattern in source colors c1,c2,c3; "
    "Panel B = transform(A) + recolor (one of rot-CW/180/CCW, flip-LR/UD, "
    "transpose, anti-transpose, then c1→t1,c2→t2,c3→t3); Panel C = a different "
    "random N×N pattern in the same source palette. Rule: infer the transform "
    "and color-map from A↔B and apply both to C. Output: the N×N "
    "recolor(transform(C)) prediction."
)

INVARIANTS = [
    "the input has three 3x3 panels separated by full color-8 columns",
    "panel B is a transformed and recolored copy of panel A",
    "panel C uses the same source color vocabulary as panel A",
    "the canonical rule applies the inferred transform and map to C",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "identity_transform", "identity_recolor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "transform":         {"type": "enum", "default": "rng", "valid": "r1|r2|r3|fh|fv|tr|atr"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "position_bias":     {"type": "str", "default": "three_3x3_panels",
                          "valid": "three_3x3_panels"},
    "n_distinct_colors": {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CODES = ["r1", "r2", "r3", "fh", "fv", "tr", "atr"]
_A = [(0, 0, 1), (1, 0, 1), (1, 1, 2), (2, 2, 3)]
_C = [(0, 1, 1), (1, 1, 2), (1, 2, 3), (2, 2, 3)]


def _grid_from_cells(cells, colors):
    out = full_grid(3, 3, 0)
    for r, c, slot in cells:
        out[r][c] = colors[slot - 1]
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
    # 3 panels a|b|c (b = transform+recolor of a); rule deduces the a->b transform
    # and applies it to c. Output is N x N. Was fixed 3x3 panels -> shape-locked.
    # Now panel size N and the a/c patterns vary.
    if difficulty == "easy":
        codes = ["fh", "fv", "tr"]; N = 3
    elif difficulty == "hard":
        codes = _CODES; N = rng.randint(4, 5)
    else:
        codes = _CODES; N = rng.randint(3, 5)
    code = ctx.draw_choice("transform", codes)
    source_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    target_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    mapping = dict(zip(source_colors, target_colors))
    a = _rand_panel(rng, N, source_colors, require_all_colors=True)
    b = _recolor(_xform_grid(a, code), mapping)
    c = _rand_panel(rng, N, source_colors, require_all_colors=True)

    W = 3 * (N + 1) - 1
    g = full_grid(N, W, 0)
    for sep in (N, 2 * N + 1):
        for r in range(N):
            g[r][sep] = 8
    for idx, panel in enumerate([a, b, c]):
        left = idx * (N + 1)
        for r in range(N):
            for c in range(N):
                g[r][left + c] = panel[r][c]
    return g


def _rand_panel(rng, n, colors, *, require_all_colors=False):
    """Random n x n panel, ~half the cells a random source color (>=3 non-zero)."""
    for _ in range(80):
        out = [[(rng.choice(colors) if rng.random() < 0.5 else 0)
                for _ in range(n)] for _ in range(n)]
        used = {v for row in out for v in row if v}
        if sum(1 for row in out for v in row if v) >= 3 and (not require_all_colors or set(colors) <= used):
            return out
    out = full_grid(n, n, 0)
    anchors = [(0, 0), (0, n - 1), (n - 1, 0)]
    for (r, c), color in zip(anchors, colors):
        out[r][c] = color
    return out


def _draw_from_degenerate(name, rng):
    g = full_grid(3, 11, 0)
    if name == "no_dividers":
        for r, c, slot in _A:
            g[r][c] = 4 + (slot - 1)
        return g
    if name == "identity_transform":
        for sep in (3, 7):
            for r in range(3):
                g[r][sep] = 8
        for r, c, slot in _A:
            color = 4 + (slot - 1)
            g[r][c] = color
            g[r][4 + c] = color
        for r, c, slot in _C:
            g[r][8 + c] = 4 + (slot - 1)
        return g
    if name == "identity_recolor":
        for sep in (3, 7):
            for r in range(3):
                g[r][sep] = 8
        for r, c, slot in _A:
            color = 4 + (slot - 1)
            g[r][c] = color
            g[r][4 + c] = color
        for r, c, slot in _C:
            g[r][8 + c] = 4 + (slot - 1)
        return g
    return g
def _panel(grid, idx):
    n = len(grid)
    left = idx * (n + 1)
    return [row[left:left + n] for row in grid]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    n = len(grid)
    w = len(grid[0])
    if n < 3 or w != 3 * (n + 1) - 1:
        errors.append(f"expected three N×N panels separated by divider columns, got {n}x{w}")
        return errors
    for sep in (n, 2 * n + 1):
        if any(row[sep] != 8 for row in grid):
            errors.append("divider columns must be full color 8")
            break
    panels = [_panel(grid, i) for i in range(3)]
    if any(sum(v != 0 for row in panel for v in row) < 3 for panel in panels):
        errors.append("all panels need at least three nonzero cells")
    source_colors = {v for row in panels[0] for v in row if v not in (0, 8)}
    query_colors = {v for row in panels[2] for v in row if v not in (0, 8)}
    if not query_colors <= source_colors:
        errors.append("panel C uses colors outside panel A's source palette")
    # B should have the same nonzero support size as a transformed A.
    if sum(v != 0 for row in panels[0] for v in row) != sum(v != 0 for row in panels[1] for v in row):
        errors.append("panel B support size does not match transformed panel A")
    return errors
