"""Generator for arc_puzzle_bank_21_set19_s:S19_H5 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1df78fa6eb8c"
VERSION = "3.1.0"  # strengthen panel-pair/query self_check invariants
TASK_ID = "1df78fa6eb8c"

SUMMARY = (
    "0-bg grid (h~4-5, w "
    "derived) with N=5-6 same-"
    "height PANELS each of "
    "width 4, separated by "
    "FULL COLOR-9 (maroon) "
    "DIVIDER COLUMNS of width "
    "1. Each panel holds a "
    "CONNECTED MOTIF of 1-3 "
    "cells in some non-{0, 9} "
    "color (color chosen "
    "independently from {2, "
    "3, 4, 5, 6, 7}). Output "
    "uniq_out=12 (intrinsic — "
    "pair-indication output "
    "normalizes across "
    "samples). Rule (FIND THE "
    "MATCHING PAIR ACROSS "
    "PANELS): identify the N "
    "PANELS separated by 9-"
    "dividers. Detect WHICH "
    "TWO PANELS share the "
    "same NORMALIZED MOTIF "
    "SHAPE (modulo D4 if "
    "task-specific). EMIT a "
    "MARKER OUTPUT — "
    "typically a smaller "
    "grid or recolored slice "
    "highlighting the pair "
    "(e.g., indices, "
    "concatenated motifs, or "
    "matrix). Net: locate "
    "the unique shape-pair "
    "among 5-6 panels and "
    "emit its identification."
)

INVARIANTS = [
    "background is 0",
    "panels separated by full color-9 columns of width 4",
    "each panel has a small motif (1-3 cells) in some non-{0, 9} color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "n_panels":       {"type": "int", "default": "rng 5..6", "valid": "4..7"},
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        panel_h = ctx.draw_int("panel_h", 4, 4)
        n = ctx.draw_int("n_panels", 4, 5)
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 5)
        n = ctx.draw_int("n_panels", 6, 7)
    else:
        panel_h = ctx.draw_int("panel_h", 4, 5)
        n = ctx.draw_int("n_panels", 5, 6)
    rng = ctx.draw_rng("layout")

    # Rule contract: split on 9-columns; the LAST panel is the QUERY; the
    # remaining panels group into consecutive PAIRS (p0,p1),(p2,p3); the answer
    # is the pair whose FIRST panel's motif matches the query's shape (dihedral).
    # So the panel count must be ODD (pair-up of n-1 needs n-1 even, else the
    # rule's (rest (rest xs)) hits '() and crashes). We plant the query's shape
    # on exactly ONE pair-first and give every other pair-first a DIFFERENT
    # shape class, so the answer is unique. Width 5n-1 <= 30 -> n in {3, 5}.
    shapes = [
        [(0, 0)],                       # dot
        [(0, 0), (0, 1)],               # domino
        [(0, 0), (0, 1), (1, 0)],       # L-tromino
        [(0, 0), (0, 1), (0, 2)],       # I-tromino (all four dihedrally distinct)
    ]
    n = rng.choice([3, 5])
    panel_w = 4
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h): g[r][c] = 9

    npairs = (n - 1) // 2
    key = rng.randrange(len(shapes))                  # the query's shape class
    panel_shape = [rng.randrange(len(shapes)) for _ in range(n)]
    panel_shape[n - 1] = key                          # query = last panel
    match_pair = rng.randint(0, npairs - 1)
    panel_shape[2 * match_pair] = key                 # the one matching pair-first
    for j in range(npairs):                           # other pair-firsts differ
        if j != match_pair:
            panel_shape[2 * j] = rng.choice([i for i in range(len(shapes)) if i != key])

    for k in range(n):
        c0 = k * (panel_w + 1)
        cells = shapes[panel_shape[k]]
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        r0 = rng.randint(0, h - sh)
        cc = rng.randint(0, panel_w - sw)
        color = rng.choice([2, 3, 4, 5, 6, 7])        # color/position are distractors
        for r, c in cells:
            g[r0 + r][c0 + cc + c] = color
    return g


def _norm_shape(cells):
    r0 = min(r for r, _c in cells)
    c0 = min(c for _r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _d4_variants(cells):
    norm = list(_norm_shape(cells))
    def normalize(xs):
        return _norm_shape(xs)
    variants = set()
    cur = norm
    for _ in range(4):
        variants.add(normalize(cur))
        variants.add(normalize([(r, -c) for r, c in cur]))
        max_r = max(r for r, _c in cur)
        cur = [(c, max_r - r) for r, c in cur]
    return variants


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify regular 9-divided panels and a unique query-matching pair."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not div_cols:
        return ["no full color-9 divider columns"]
    if div_cols != list(range(4, w, 5)):
        errs.append("divider columns are not the expected every-5 regular panel separators")
    n_panels = len(div_cols) + 1
    if n_panels not in (3, 5) or n_panels % 2 != 1:
        errs.append(f"expected odd panel count 3 or 5, found {n_panels}")
    panel_shapes = []
    for k in range(n_panels):
        c0 = k * 5
        cells = []
        for r in range(h):
            for c in range(4):
                v = grid[r][c0 + c]
                if v == 9:
                    errs.append("color-9 leaked inside a panel")
                elif v != 0:
                    cells.append((r, c))
        if not (1 <= len(cells) <= 3):
            errs.append(f"panel {k} has motif size {len(cells)}, expected 1..3")
        panel_shapes.append(cells)
    if errs or n_panels < 3:
        return errs
    query = panel_shapes[-1]
    q_variants = _d4_variants(query)
    pair_firsts = list(range(0, n_panels - 1, 2))
    matches = [idx for idx in pair_firsts if _norm_shape(panel_shapes[idx]) in q_variants]
    if len(matches) != 1:
        errs.append(f"expected exactly one pair-first motif to match the query, found {len(matches)}")
    return errs


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
