"""Generator for 16b:hard_107 — build scale-normalized shape equivalence matrix.

Rule: 3 panels at cols [0, 7, 14] (6 wide each, full rows). Output 3x3:
8 if scale-normalized shape signatures match, else 0.

Combinatorial axes (8): panel_density, palette_kind, n_panels,
palette_size, position_bias, n_distinct_colors, scale_diversity, texture.
Degenerates: empty_panel, all_identical, no_scale_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d06efc7bef9"
VERSION = "2.1.0"  # all_background fix: n_classes=1 made all 3 panels the same scale-shape -> a UNIFORM all-8 3x3 output (degenerate, and off-distribution: the canonical task always shows exactly one matching pair, never all-match). Restrict n_classes to 2..3 so the output always has >=1 structural 0 (3 one-pair-match variants + the all-distinct matrix = 4 distinct, == baseline).
TASK_ID = "5d06efc7bef9"
SUMMARY = "Grid is 6 rows × 20 cols, divided into 3 panels of 6 cols each (cols 0-5, 7-12, 14-19) with single-column gaps. Each panel holds a single-color binary shape. Rule scale-normalizes each panel (downscale by 2 while possible), then outputs a 3×3 grid where cell (r, c) = 8 if panels r and c have the same scale-normalized shape signature, else 0. Diagonal always 8."

# Rivals: 'output is input' refuted by demos (output is 3x3).
# 'compare by raw shape, not scale-normalized' refuted by demos
# with same-shape-different-scale matching. 'use any color' refuted
# by demos (output is 0/8). 'output 3xN where N != 3' refuted by
# demos always 3x3. 3 demos with mix of matches and non-matches.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "grid is 5 rows tall and 20 cols wide",
    "3 panels each holding 3-7 non-bg cells in a single color",
]

PALETTE_KINDS = ("default", "sparse", "dense", "balanced")
DEGENERATE_TEXTURES = ("empty_panel", "all_identical", "no_scale_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse|dense|balanced"},
    "n_panels":       {"type": "int", "default": "3", "valid": "3"},
    "n_classes":      {"type": "int", "default": "rng 1..3 scale-shape classes", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse|dense|balanced|empty_panel|all_identical|no_scale_match"},
}

# small irreducible fundamentals (no 2x2-uniform structure -> can't downscale);
# distinct layouts -> distinct scale-normalized signatures (different classes never match).
_FUNDAMENTALS = [
    [(0, 0), (0, 1), (1, 0)],                       # L-tromino
    [(0, 0), (1, 1)],                               # 2-diagonal
    [(0, 0), (0, 1), (0, 2), (1, 1)],               # T
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],       # plus
    [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],       # X (3x3)
]


def _upscale(cells, s):
    return [(r * s + dr, c * s + dc) for (r, c) in cells
            for dr in range(s) for dc in range(s)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # n_classes>=2: never make all 3 panels the same class (that yields a
    # uniform all-8 output, which is degenerate and off-distribution).
    n_classes = ctx.draw_int("n_classes", 2, 3)
    rng = ctx.draw_rng("layout")
    h = 6; w = 20  # h even so downscale-by-2 works; panels 6 wide at cols 0/7/14
    starts = [0, 7, 14]
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)

    # one fundamental per class; same-class panels carry it at scale 1 or 2 (scale-
    # normalize equal -> 8); different classes -> different fundamentals -> 0.
    funds = rng.sample(_FUNDAMENTALS, n_classes)
    # Assign classes to panels via an explicit KEYED choice (spreads the output
    # partition across seeds far better than a random shuffle). n_classes==2 ->
    # exactly one matching pair, odd panel keyed in 0..2 (3 distinct outputs);
    # n_classes==3 -> all-distinct matrix (1 output). 4 distinct outputs total.
    if n_classes == 2:
        odd = ctx.draw_int("odd_panel", 0, 2)
        assign = [1 if i == odd else 0 for i in range(3)]
    else:
        assign = [0, 1, 2]

    g = full_grid(h, w, 0)
    for c0, color, cls in zip(starts, palette, assign):
        base = funds[cls]
        bh = max(r for r, _ in base) + 1; bw = max(c for _, c in base) + 1
        smax = max(1, min(h // bh, 6 // bw, 2))
        cells = _upscale(base, rng.randint(1, smax))
        for dr, dc in cells:
            if dr < h and dc < 6:
                g[dr][c0 + dc] = color
    return g


def _binary_crop(panel):
    cells = [(r, c) for r in range(len(panel)) for c in range(len(panel[0]))
             if panel[r][c] != 0]
    if not cells:
        return ((0,),)
    r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
    return tuple(tuple(1 if panel[r][c] != 0 else 0 for c in range(c1, c2 + 1))
                 for r in range(r1, r2 + 1))


def _downscale2(sig):
    h, w = len(sig), len(sig[0])
    if h % 2 or w % 2:
        return None
    for r in range(0, h, 2):
        for c in range(0, w, 2):
            v = sig[r][c]
            if not (sig[r + 1][c] == v and sig[r][c + 1] == v
                    and sig[r + 1][c + 1] == v):
                return None
    return tuple(tuple(sig[2 * r][2 * c] for c in range(w // 2))
                 for r in range(h // 2))


def _signature(panel):
    sig = _binary_crop(panel)
    while True:
        ds = _downscale2(sig)
        if ds is None:
            return sig
        sig = _binary_crop([list(row) for row in ds])


def self_check(grid, *, difficulty=None, meta=None):
    """Each of the 3 panels holds a non-empty shape, and the panels are NOT
    all the same scale-normalized signature (which would yield a degenerate
    uniform all-8 output)."""
    if len(grid[0]) < 20:
        return ["grid must be >=20 cols (3 panels at cols 0/7/14)"]
    panels = [[row[s:s + 6] for row in grid] for s in (0, 7, 14)]
    msgs = []
    for i, p in enumerate(panels):
        if not any(v != 0 for row in p for v in row):
            msgs.append(f"panel {i} is empty")
    sigs = [_signature(p) for p in panels]
    if len(set(sigs)) == 1:
        msgs.append("all 3 panels share one signature -> uniform all-8 output")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 5, 20
    g = full_grid(h, w, 0)
    starts = [0, 7, 14]
    if name == "empty_panel":
        # one panel empty — scale signature undefined
        for r, c in [(0, 0), (1, 1), (2, 2)]:
            g[r][c] = 1
        # middle panel empty
        for r, c in [(0, 14), (1, 15)]:
            g[r][c] = 3
        return g
    if name == "all_identical":
        # all 3 panels same shape at same scale — full match (trivial)
        for c0, color in zip(starts, [1, 2, 3]):
            for r, dc in [(0, 0), (1, 0), (1, 1)]:
                g[r][c0 + dc] = color
        return g
    if name == "no_scale_match":
        # 3 panels with totally different normalized shapes
        for r, dc in [(0, 0), (1, 0), (2, 0)]:
            g[r][0 + dc] = 1
        for r, dc in [(0, 0), (0, 1), (0, 2), (0, 3)]:
            g[r][7 + dc] = 2
        for r, dc in [(0, 0), (1, 1), (2, 2), (3, 3), (1, 0)]:
            g[r][14 + dc] = 3
        return g
    return g
