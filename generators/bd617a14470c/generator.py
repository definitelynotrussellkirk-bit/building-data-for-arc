"""Generator for arc_puzzle_bank_eleventh21:H76 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd617a14470c"
# 1.3.0: enforce the ANALOGY semantics the rule actually reads. Was: 5-7
# panels each with INDEPENDENT random motifs (P1->P2 almost never a real
# transform, P3->P4 almost never a real recolor -> the inferred transform
# fell into the #f/else branch, a broken puzzle). Now: square panels with
# P2 = chosen transform(P1), P4 = recolor(P3), and P5 a fresh motif using
# P3's source colours so the recolor applies. Exactly 5 panels.
VERSION = "1.3.2"  # panel size capped at 5 (w=5s+4 must fit 30; hard's s=6 overflowed on every draw)
TASK_ID = "bd617a14470c"

SUMMARY = (
    "5 SQUARE panels separated by full color-9 divider columns. Panels 1->2 "
    "are related by a geometric TRANSFORM (id/rot90/rot180/rot270/flip-h/"
    "flip-v/transpose); panels 3->4 by a COLOR RECOLOR of the same shape; "
    "panel 5 is a fresh motif using panel 3's source colours. Rule: infer "
    "the transform from 1->2 and the recolor from 3->4, apply both to panel "
    "5, output the result."
)

INVARIANTS = [
    "background is 0",
    "panels separated by full-height color-9 divider columns (1 col wide)",
    "panels are square so geometric transforms preserve panel dims",
    "panel2 = transform(panel1); panel4 = recolor(panel3)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 3..5 (square)", "valid": "3..5"},
    "n_panels":       {"type": "int", "default": "5 (fixed by rule)", "valid": "5..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "horizontal_panels_9divs",
                       "valid": "horizontal_panels_9divs"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_dividers|empty_panels|single_panel"},
}


def _build_motif(rng, k, bound=None):
    # bound (when given) caps the motif's bbox to bound×bound so it fits the panel;
    # the old unbounded walk could grow a k-cell line taller/wider than s, making
    # _rand_panel's randint(0, s - sh) collapse (randrange(0, -1)).
    cells = [(0, 0)]; seen = {(0, 0)}
    attempts = 0
    while len(cells) < k and attempts < 4000:
        attempts += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) in seen:
            continue
        if bound is not None:
            rs = [p[0] for p in cells]; cs = [p[1] for p in cells]
            if max(max(rs), nr) - min(min(rs), nr) + 1 > bound:
                continue
            if max(max(cs), nc) - min(min(cs), nc) + 1 > bound:
                continue
        cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _xform(panel, name):
    """Apply a named transform to a square panel (list[list])."""
    s = len(panel)
    if name == 'id':
        return [row[:] for row in panel]
    if name == 'rot90':   # clockwise
        return [[panel[s - 1 - c][r] for c in range(s)] for r in range(s)]
    if name == 'rot180':
        return [[panel[s - 1 - r][s - 1 - c] for c in range(s)] for r in range(s)]
    if name == 'rot270':  # ccw
        return [[panel[c][s - 1 - r] for c in range(s)] for r in range(s)]
    if name == 'flip-h':  # left-right
        return [row[::-1] for row in panel]
    if name == 'flip-v':  # up-down
        return panel[::-1]
    if name == 'transpose':
        return [[panel[c][r] for c in range(s)] for r in range(s)]
    raise ValueError(name)


def _rand_panel(rng, s, colors, k):
    """Square s×s panel with a k-cell connected motif in given colours."""
    p = [[0] * s for _ in range(s)]
    cells = _build_motif(rng, k, bound=s)
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    top = rng.randint(0, s - sh); left = rng.randint(0, s - sw)
    for r, c in cells:
        p[top + r - min(rs)][left + c - min(cs)] = rng.choice(colors)
    return p


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has full color-9 divider columns separating 5 equal panels."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 40 or w > 40:
        errs.append(f"grid too large: {h}x{w}")
    full_9_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    has_nine = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    if not has_nine:
        return errs  # degenerate no_dividers
    if len(full_9_cols) < 4:
        errs.append(f"expected >=4 full color-9 divider cols (for 5 panels), got {len(full_9_cols)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # ARC cap: 5 panels of s x s + 4 dividers -> w = 5s+4 <= 30 -> s <= 5
    # (the old hard band's s=6 emitted 34-wide grids; validity sweep)
    if difficulty == "easy":
        s = ctx.draw_int("panel_h", 3, 3)
    elif difficulty == "hard":
        s = ctx.draw_int("panel_h", 5, 5)
    else:
        s = ctx.draw_int("panel_h", 3, 5)
    rng = ctx.draw_rng("layout")

    n = 5  # the rule reads exactly 5 panels (transform pair, recolor pair, query)
    transforms = ['id', 'rot90', 'rot180', 'rot270', 'flip-h', 'flip-v', 'transpose']
    tname = rng.choice(transforms)

    # Pair 1->2: P2 = transform(P1).
    src_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 3)
    p1 = _rand_panel(rng, s, src_colors, rng.randint(2, max(2, s * s // 2)))
    p2 = _xform(p1, tname)

    # Pair 3->4: P4 = recolor(P3). P3 uses a set of source colours; map each
    # to a distinct target colour.
    p3_pal = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 2)
    p3 = _rand_panel(rng, s, p3_pal, rng.randint(2, max(2, s * s // 2)))
    used = sorted({v for row in p3 for v in row if v != 0})
    avail = [c for c in range(1, 9) if c not in used]
    rng.shuffle(avail)
    cmap = {v: avail[i] for i, v in enumerate(used)}
    p4 = [[cmap.get(v, v) if v != 0 else 0 for v in row] for row in p3]

    # Panel 5: fresh motif using P3's SOURCE colours so the recolor applies.
    p5 = _rand_panel(rng, s, used if used else p3_pal,
                     rng.randint(2, max(2, s * s // 2)))

    panels = [p1, p2, p3, p4, p5]
    # Assemble with 1-wide full color-9 divider columns.
    h = s
    w = s * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(n):
        c0 = k * (s + 1)
        for r in range(s):
            for c in range(s):
                g[r][c0 + c] = panels[k][r][c]
        if k < n - 1:
            div = c0 + s
            for r in range(h):
                g[r][div] = 9
    return g


def _draw_from_degenerate(name, rng):
    panel_h, n, panel_w = 4, 5, 4
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        for k in range(n):
            c0 = k * panel_w
            g[1][c0 + 1] = [4, 6, 7, 4, 6][k]
        return g
    if name == "empty_panels":
        for k in range(1, n):
            c = panel_w * k + (k - 1)
            for r in range(h): g[r][c] = 9
        return g
    if name == "single_panel":
        g[1][1] = 4
        return g
    return g
