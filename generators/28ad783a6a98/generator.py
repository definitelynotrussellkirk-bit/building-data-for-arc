"""Generator for arc_puzzle_bank_twentythird21:H161 — compose two 4x4 transforms on 5th panel.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: identity_first (panel 1 == panel 2 → t1 is identity),
identity_second (panel 3 == panel 4 → t2 is identity), no_dividers
(no color-8 separators → rule's 5-panel split fails).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28ad783a6a98"
VERSION = "3.1.0"  # canonical 4x4 single-component panels restored
TASK_ID = "28ad783a6a98"
SUMMARY = (
    "4×24 grid with FIVE 4×4 PANELS separated by 1-wide full-height color-8 "
    "columns. Panels: A, A'=t1(A), C, C'=t2(C), X. A/C/X are each a "
    "single-color connected asymmetric motif, matching the canonical low-object-count "
    "distribution while keeping the demonstrated dihedral transforms unambiguous. "
    "Rule: split panels by color-8 columns; infer t1 and t2; output t2(t1(X))."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the input has five 4x4 panels separated by 1-wide color-8 columns",
    "panel 2 is an exact transform of panel 1 (under one of 7 dihedral codes)",
    "panel 4 is an exact transform of panel 3 (under one of 7 dihedral codes)",
    "panel motifs are connected single-color asymmetric components",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_first", "identity_second", "no_dividers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "first_transform":   {"type": "enum", "default": "rng",
                          "valid": "r1|r2|r3|fh|fv|tr|atr"},
    "second_transform":  {"type": "enum", "default": "rng",
                          "valid": "r1|r2|r3|fh|fv|tr|atr"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "five_panels_two_transforms",
                          "valid": "five_panels_two_transforms"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse_connected", "valid": "sparse_connected"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify canonical 4x24 five-panel layout and transform demonstrations."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("identity_first", "identity_second", "no_dividers"):
        return []
    errs = []
    if (h, w) != (4, 24):
        errs.append(f"expected canonical 4x24 grid, got {(h, w)}")
    div_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if div_cols != [4, 9, 14, 19]:
        errs.append(f"expected divider columns [4, 9, 14, 19], found {div_cols}")
    panels = _split_panels(grid)
    if len(panels) == 5:
        for i, panel in enumerate(panels):
            colors = sorted({v for row in panel for v in row if v != 0})
            if len(colors) != 1:
                errs.append(f"panel {i} should contain one non-bg motif color, found {colors}")
            comps = _components(panel)
            if len(comps) != 1:
                errs.append(f"panel {i} should contain exactly one connected motif, found {len(comps)}")
        if panels[1] not in [_xform_grid(panels[0], code) for code in _CODES]:
            errs.append("panel 2 is not a supported transform of panel 1")
        if panels[3] not in [_xform_grid(panels[2], code) for code in _CODES]:
            errs.append("panel 4 is not a supported transform of panel 3")
    return errs


_CODES = ["r1", "r2", "r3", "fh", "fv", "tr", "atr"]
_A = [
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]
_C = [
    [2, 2, 0, 0],
    [2, 2, 2, 0],
    [0, 0, 2, 0],
    [0, 0, 0, 0],
]
_X = [
    [3, 3, 0, 0],
    [0, 3, 0, 0],
    [0, 3, 0, 0],
    [0, 0, 0, 0],
]


def _xform_grid(grid, code):
    h = len(grid)
    w = len(grid[0])
    if code == "r1":
        return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == "r2":
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if code == "r3":                       # rotate ccw (square panels)
        return [[grid[c][h - 1 - r] for c in range(w)] for r in range(h)]
    if code == "fh":
        return [list(reversed(row)) for row in grid]
    if code == "fv":
        return list(reversed([row[:] for row in grid]))
    if code == "tr":
        return [[grid[r][c] for r in range(h)] for c in range(w)]
    return [[grid[w - 1 - c][h - 1 - r] for c in range(w)] for r in range(h)]  # anti-transpose


def _recolor(grid, mapping):
    return [[mapping.get(v, v) for v in row] for row in grid]


def _paste_panel(out, panel, grid, p):
    left = panel * (p + 1)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            out[r][left + c] = value


def _components(panel):
    h, w = len(panel), len(panel[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if panel[r][c] == 0 or (r, c) in seen:
                continue
            color = panel[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen
                            and panel[nx][ny] == color):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            comps.append((color, cells))
    return comps


def _split_panels(grid):
    if len(grid) != 4 or len(grid[0]) != 24:
        return []
    return [[[grid[r][k * 5 + c] for c in range(4)] for r in range(4)]
            for k in range(5)]


def _rand_asym(rng, p, color):
    """Connected single-color p×p motif with trivial dihedral stabilizer."""
    for _ in range(500):
        target = rng.randint(3, min(6, p * p - 1))
        cells = {(rng.randrange(p), rng.randrange(p))}
        while len(cells) < target:
            r, c = rng.choice(tuple(cells))
            dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            nr, nc = r + dr, c + dc
            if 0 <= nr < p and 0 <= nc < p:
                cells.add((nr, nc))
        grid = [[color if (r, c) in cells else 0 for c in range(p)] for r in range(p)]
        forms = {tuple(tuple(row) for row in grid)}
        for code in _CODES:
            forms.add(tuple(tuple(row) for row in _xform_grid(grid, code)))
        if len(forms) == 8:
            return grid
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    p = 4
    t1 = ctx.draw_choice("first_transform", _CODES)
    t2 = ctx.draw_choice("second_transform", _CODES)
    colors = ctx.draw_distinct_colors("panel_colors", n=3, exclude={0, 8})
    for _outer in range(80):
        a = _rand_asym(rng, p, colors[0])
        c = _rand_asym(rng, p, colors[1])
        x = _rand_asym(rng, p, colors[2])
        if a is None or c is None or x is None:
            continue
        # Avoid one-seed demos where the composed transform leaves X unchanged.
        if _xform_grid(_xform_grid(x, t1), t2) == x:
            valid_t2 = [code for code in _CODES
                        if _xform_grid(_xform_grid(x, t1), code) != x]
            t2 = rng.choice(valid_t2)
        panels = [a, _xform_grid(a, t1), c, _xform_grid(c, t2), x]
        width = 5 * p + 4
        g = full_grid(p, width, 0)
        for k in range(1, 5):
            sep = k * (p + 1) - 1
            for r in range(p):
                g[r][sep] = 8
        for idx, panel in enumerate(panels):
            _paste_panel(g, idx, panel, p)
        return g
    raise ValueError("could not realize asymmetric connected panel motifs")


def _draw_from_degenerate(name, rng):
    g = full_grid(4, 24, 0)
    def fill_dividers():
        for sep in (4, 9, 14, 19):
            for r in range(4):
                g[r][sep] = 8
    if name == "identity_first":
        # Panel 1 == Panel 2 → t1 is identity.
        fill_dividers()
        _paste_panel(g, 0, _A, 4)
        _paste_panel(g, 1, _A, 4)   # identity
        _paste_panel(g, 2, _C, 4)
        _paste_panel(g, 3, _xform_grid(_C, "r1"), 4)
        _paste_panel(g, 4, _X, 4)
        return g
    if name == "identity_second":
        # Panel 3 == Panel 4 → t2 is identity.
        fill_dividers()
        _paste_panel(g, 0, _A, 4)
        _paste_panel(g, 1, _xform_grid(_A, "fh"), 4)
        _paste_panel(g, 2, _C, 4)
        _paste_panel(g, 3, _C, 4)   # identity
        _paste_panel(g, 4, _X, 4)
        return g
    if name == "no_dividers":
        # No color-8 separators — rule's 5-panel split fails.
        _paste_panel(g, 0, _A, 4)
        _paste_panel(g, 1, _xform_grid(_A, "fh"), 4)
        _paste_panel(g, 2, _C, 4)
        _paste_panel(g, 3, _xform_grid(_C, "r1"), 4)
        _paste_panel(g, 4, _X, 4)
        return g
    return g
