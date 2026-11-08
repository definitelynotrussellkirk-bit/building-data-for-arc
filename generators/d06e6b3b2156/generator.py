"""Generator for arc_additional_puzzles_21_set14_bundle:M97.

Rule: the translation vector is (last color-9 cell) - (last color-8
cell). Translate every non-{0,8,9} cell (the MOTIF) by that vector and
paint it on a fresh grid (in-bounds cells only); the anchor/target are
consumed.

Combinatorial axes: grid size, the motif (shape + colors), the anchor
position, and the target position (which sets the vector).
Degenerates: no_anchor, no_target, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d06e6b3b2156"
VERSION = "2.0.1"  # diversity: random motif + anchor/target (vector) + grid (was fixed ~9)
TASK_ID = "d06e6b3b2156"
SUMMARY = (
    "0-bg grid (size varies) with ONE color-8 (cyan) ANCHOR, ONE color-9 "
    "(maroon) TARGET, and a MOTIF of 3-7 cells in colors from {1..7}. "
    "Rule: translate the motif by (target - anchor) and paint it on a "
    "fresh grid (anchor + target consumed). The motif is placed so its "
    "translation lands fully in-bounds. The grid size, the motif "
    "shape/colors, and the anchor/target positions (hence the vector) all "
    "vary freely (was a fixed motif + fixed anchor/target, ~9 distinct)."
)

INVARIANTS = [
    "exactly one color-8 anchor and one color-9 target",
    "a motif of 3-7 non-{0,8,9} cells, disjoint from anchor/target",
    "the motif translated by (target-anchor) lands fully in-bounds",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_anchor", "no_target", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = (1, 2, 3, 4, 5, 6, 7)  # non-0 bg, non-8 anchor, non-9 target

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_anchor|no_target|full_grid"},
}


def _conn_poly(rng, size, maxd):
    for _ in range(80):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        n = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-8 anchor, one color-9 target, ≥3 motif cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    counts = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            counts[v] = counts.get(v, 0) + 1
    if counts.get(8, 0) != 1:
        errs.append(f"expected exactly 1 color-8 anchor; found {counts.get(8,0)}")
    if counts.get(9, 0) != 1:
        errs.append(f"expected exactly 1 color-9 target; found {counts.get(9,0)}")
    motif_cells = sum(v for k, v in counts.items() if k not in (0, 8, 9))
    if motif_cells < 3:
        errs.append(f"expected ≥3 motif cells (non-{{0,8,9}}); found {motif_cells}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, szr, md = (8, 10), (9, 11), (3, 5), 3
    elif difficulty == "hard":
        hr, wr, szr, md = (11, 14), (12, 16), (4, 7), 4
    else:
        hr, wr, szr, md = (9, 12), (10, 14), (3, 6), 4

    for _attempt in range(50):
        h = rng.randint(*hr); w = rng.randint(*wr)
        motif = _conn_poly(rng, rng.randint(*szr), md)
        mh = max(r for r, c in motif) + 1; mw = max(c for r, c in motif) + 1
        # vector: keep small enough that motif fits before AND after
        dr = rng.randint(-(h - mh), h - mh)
        dc = rng.randint(-(w - mw), w - mw)
        if dr == 0 and dc == 0:
            continue
        # placement window so both motif and motif+vector are in-bounds
        rlo = max(0, -dr); rhi = min(h - mh, h - mh - dr)
        clo = max(0, -dc); chi = min(w - mw, w - mw - dc)
        if rlo > rhi or clo > chi:
            continue
        mt = rng.randint(rlo, rhi); ml = rng.randint(clo, chi)
        ncol = rng.randint(1, 3)
        palette = rng.sample(_COLORS, ncol)

        g = full_grid(h, w, 0)
        occ = set()
        for (r, c) in motif:
            rr, cc = mt + r, ml + c
            g[rr][cc] = rng.choice(palette)
            occ.add((rr, cc))

        # anchor A (8) + target A+vector (9), both free and in-bounds
        placed = False
        for _t in range(60):
            ar = rng.randint(0, h - 1); ac = rng.randint(0, w - 1)
            tr, tc = ar + dr, ac + dc
            if not (0 <= tr < h and 0 <= tc < w):
                continue
            if (ar, ac) in occ or (tr, tc) in occ or (ar, ac) == (tr, tc):
                continue
            g[ar][ac] = 8
            g[tr][tc] = 9
            placed = True
            break
        if placed:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 10, 0)
    if name == "no_anchor":
        g[5][6] = 9
        return g
    if name == "no_target":
        g[1][1] = 8
        g[2][2] = 2
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(10):
                g[r][c] = 2
        return g
    return g
