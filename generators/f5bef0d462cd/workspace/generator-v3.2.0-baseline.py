"""Generator for arc_puzzle_bank_eleventh21:H71 — analogy transform across 3 panels.

Rule: full color-9 columns split the grid into three 4x4 panels.  Infer the
canonical transform T mapping panel0 -> panel1, then apply T to panel2.

Canonical examples are sparse: panel0 and panel1 contain the same single-color
motif, panel2 contains one motif in a different color, and the two color-9
divider columns are full-height.  This generator stays in that sparse object-count
regime while keeping the transform unambiguous.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f5bef0d462cd"
VERSION = "3.2.0"  # canonical sparse 4x4 motif panels
TASK_ID = "f5bef0d462cd"
SUMMARY = (
    "Three sparse 4x4 panels separated by full color-9 divider columns. panel1 is "
    "a canonical transform T of panel0; panel0 uses one non-9 color and is "
    "asymmetric so T is unambiguous. panel2 is a second sparse motif in a different "
    "color. Rule: infer T from panel0->panel1 and output T(panel2)."
)

INVARIANTS = [
    "exactly three 4x4 panels separated by two full-height color-9 divider columns",
    "panel1 == T(panel0) for exactly one canonical transform T",
    "panel0/panel1 share one non-9 color; panel2 uses a different non-9 color",
    "panel cells are sparse and never use color 9",
    "output = T(panel2)",
]

DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
_CELL_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)   # never 9 (separator)

# Same order as the canonical rule's e11-transform-order.
def _rot_cw(g):  return [list(row) for row in zip(*g[::-1])]
def _rot_ccw(g): return [list(row) for row in zip(*g)][::-1]
def _rot180(g):  return [row[::-1] for row in g[::-1]]
def _flip_lr(g): return [row[::-1] for row in g]
def _flip_ud(g): return g[::-1]
def _transpose(g): return [list(row) for row in zip(*g)]

_TRANSFORMS = [
    ("id", lambda g: [row[:] for row in g]),
    ("rot90", _rot_cw), ("rot180", _rot180), ("rot270", _rot_ccw),
    ("flip-h", _flip_lr), ("flip-v", _flip_ud),
    ("transpose", _transpose),
]

AXES = {
    "panel_k":   {"type": "int", "default": "4", "valid": "4"},
    "transform": {"type": "str", "default": "rng canonical order", "valid": "id|rot90|rot180|rot270|flip-h|flip-v|transpose"},
    "fill":      {"type": "float", "default": "sparse motif", "valid": "3..5 cells per panel motif"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":   {"type": "str", "default": "sparse_motifs", "valid": "sparse_motifs"},
    "texture":   {"type": "str", "default": "sparse_motifs", "valid": "|".join(("sparse_motifs",) + DEGENERATE_TEXTURES)},
}

# Connected 4x4 motifs.  They are deliberately asymmetric after placement so the
# canonical transform inference has one match.
_PATTERNS = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 2), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 1), (1, 1), (2, 1), (2, 2)),
    ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
)


def _tuplize(g):
    return tuple(tuple(row) for row in g)


def _blank_panel(k=4):
    return full_grid(k, k, 0)


def _paint_pattern(pattern, color, *, k=4):
    g = _blank_panel(k)
    for r, c in pattern:
        g[r][c] = color
    return g


def _asymmetric(g):
    return len({_tuplize(fn(g)) for _, fn in _TRANSFORMS}) == len(_TRANSFORMS)


def _panel_colors(panel):
    return {v for row in panel for v in row if v not in (0, 9)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    rng = ctx.draw_rng("layout")
    k = 4
    colors = list(ctx.draw_distinct_colors("colors", n=2, exclude={0, 9}))
    name, tfn = rng.choice(_TRANSFORMS)

    for _attempt in range(80):
        p0_pat = rng.choice(_PATTERNS)
        p2_pat = rng.choice(_PATTERNS)
        panel0 = _paint_pattern(p0_pat, colors[0], k=k)
        if not _asymmetric(panel0):
            continue
        panel1 = [list(row) for row in tfn(panel0)]
        panel2 = _paint_pattern(p2_pat, colors[1], k=k)
        g = full_grid(k, 3 * k + 2, 0)
        for pi, panel in enumerate((panel0, panel1, panel2)):
            c0 = pi * (k + 1)
            for r in range(k):
                for c in range(k):
                    g[r][c0 + c] = panel[r][c]
        for sep in (k, 2 * k + 1):
            for r in range(k):
                g[r][sep] = 9
        return g

    # deterministic fallback: a clearly asymmetric 4x4 with rot90
    panel0 = _paint_pattern(_PATTERNS[0], 2)
    panel1 = _rot_cw(panel0)
    panel2 = _paint_pattern(_PATTERNS[1], 3)
    g = full_grid(4, 14, 0)
    for pi, panel in enumerate((panel0, panel1, panel2)):
        c0 = pi * 5
        for r in range(4):
            for c in range(4):
                g[r][c0 + c] = panel[r][c]
    for sep in (4, 9):
        for r in range(4):
            g[r][sep] = 9
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(4, 14, 0)
    p0 = _paint_pattern(_PATTERNS[0], 2)
    if name == "no_dividers":
        for r in range(4):
            for c in range(4):
                g[r][c] = p0[r][c]
        return g
    if name == "empty_panels":
        for sep in (4, 9):
            for r in range(4):
                g[r][sep] = 9
        return g
    if name == "single_panel":
        for r in range(4):
            for c in range(4):
                g[r][c] = p0[r][c]
        return g
    return g


def _split_panels(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(div_cols) != 2:
        return None
    cuts = [0, div_cols[0] + 1, div_cols[1] + 1, w + 1]
    panels = [
        [row[cuts[0]:div_cols[0]] for row in grid],
        [row[cuts[1]:div_cols[1]] for row in grid],
        [row[cuts[2]:w] for row in grid],
    ]
    return panels, div_cols


def self_check(grid, *, difficulty=None, meta=None):
    """Three sparse square panels separated by full-height color-9 dividers."""
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty rectangular list-of-lists"]
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]

    split = _split_panels(grid)
    if split is None:
        return ["expected exactly two full-height color-9 divider columns"]
    panels, div_cols = split
    if div_cols != [h, 2 * h + 1]:
        errs.append(f"expected dividers at panel boundaries {[h, 2 * h + 1]}, got {div_cols}")
    if w != 3 * h + 2:
        errs.append(f"expected three hxh panels plus two dividers, got {h}x{w}")

    for i, panel in enumerate(panels):
        if len(panel) != h or any(len(row) != h for row in panel):
            errs.append(f"panel {i} should be square {h}x{h}")
        if any(v == 9 for row in panel for v in row):
            errs.append(f"panel {i} should not contain separator color 9")
        nz = sum(1 for row in panel for v in row if v not in (0, 9))
        if not (3 <= nz <= 5):
            errs.append(f"panel {i} should be sparse with 3..5 colored cells, got {nz}")

    if len(panels) == 3:
        p0, p1, p2 = panels
        matches = [name for name, fn in _TRANSFORMS if fn(p0) == p1]
        if len(matches) != 1:
            errs.append(f"expected exactly one transform mapping panel0 to panel1, got {matches}")
        colors01 = _panel_colors(p0) | _panel_colors(p1)
        colors2 = _panel_colors(p2)
        if len(colors01) != 1:
            errs.append(f"panel0/panel1 should share one motif color, got {sorted(colors01)}")
        if len(colors2) != 1:
            errs.append(f"panel2 should use one motif color, got {sorted(colors2)}")
        if colors01 & colors2:
            errs.append("panel2 color should differ from panel0/panel1 color")
    return errs
