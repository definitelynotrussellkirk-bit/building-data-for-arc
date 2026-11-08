"""Generator for additional_scaffolded:M5.

Rule: find the full-column color-9 AXIS. For each empty cell on the RIGHT
of the axis whose mirror cell on the left (across the axis) is a
non-{0,9} color, copy that color over. Net: the left-side blobs are
mirrored to the right.

Combinatorial axes: grid size, axis column, and the left-side blobs
(count / shapes / colors / positions).
Degenerates: no_axis, no_blob, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f3be696a1ae4"
VERSION = "2.2.0"  # add executable invariant self_check; hard may use 4 blobs
TASK_ID = "f3be696a1ae4"
SUMMARY = (
    "0-bg grid (size varies) with ONE full-column color-9 (maroon) AXIS "
    "and 1-4 colored BLOBS on the LEFT side (colors from {1..8}, placed "
    "within mirror range so their reflections land in-bounds), none on "
    "the right. Rule: mirror each left blob across the axis to the right "
    "(copy the left color into the empty mirror cell). The grid size, "
    "axis column, and the blobs' shapes/colors/positions all vary freely "
    "(was a fixed axis + 2 fixed blobs, ~9 distinct)."
)

INVARIANTS = [
    "exactly one full-column color-9 axis with room on both sides",
    "1-4 non-{0,9} blobs only on the left, within mirror range",
    "the right side is empty (it receives the mirror)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_axis", "no_blob", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)  # non-0 bg, non-9 axis

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_axis|no_blob|full_grid"},
}


def _conn_poly(rng, size, maxd):
    for _ in range(60):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        n = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (1, 0)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nbr, szr, maxd = (6, 8), (7, 9), (1, 2), (2, 3), 3
    elif difficulty == "hard":
        hr, wr, nbr, szr, maxd = (9, 14), (11, 16), (2, 4), (3, 6), 4
    else:
        hr, wr, nbr, szr, maxd = (7, 10), (9, 13), (2, 3), (2, 5), 4

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        axis = rng.randint(2, w - 3)
        # left mirror-able columns: lc with mirror 2*axis-lc in [0,w-1]
        lc_lo = max(0, 2 * axis - (w - 1)); lc_hi = axis - 1
        if lc_lo > lc_hi:
            continue
        g = full_grid(h, w, 0)
        for r in range(h):
            g[r][axis] = 9
        occ = [[False] * w for _ in range(h)]
        for c in range(w):
            occ[r][axis] = True
        for r2 in range(h):
            occ[r2][axis] = True

        placed = 0
        colors = rng.sample(_COLORS, min(rng.randint(*nbr), len(_COLORS)))
        for col in colors:
            shape = _conn_poly(rng, rng.randint(*szr), maxd)
            bh = max(r for r, c in shape) + 1; bw = max(c for r, c in shape) + 1
            if bh > h or bw > (lc_hi - lc_lo + 1):
                continue
            for _t in range(30):
                top = rng.randint(0, h - bh); left = rng.randint(lc_lo, lc_hi - bw + 1)
                cells = [(top + r, left + c) for r, c in shape]
                if all(0 <= rr < h and 0 <= cc < w and not occ[rr][cc] for rr, cc in cells):
                    for rr, cc in cells:
                        g[rr][cc] = col; occ[rr][cc] = True
                    placed += 1
                    break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 8, 0)
    if name == "no_axis":
        g[1][1] = 2
        return g
    if name == "no_blob":
        for r in range(7):
            g[r][4] = 9
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(8):
                g[r][c] = 9
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    full_axes = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(full_axes) != 1:
        errs.append(f"expected exactly one full 9-axis column, found {len(full_axes)}")
        return errs
    axis = full_axes[0]
    if axis <= 0 or axis >= w - 1:
        errs.append("9-axis must leave room on both sides")
    colored = []
    for r, row in enumerate(grid):
        if len(row) != w:
            errs.append("ragged grid")
            return errs
        for c, v in enumerate(row):
            if v == 9 and c != axis:
                errs.append("9 appears outside the full guide axis")
            elif v not in (0, 9):
                colored.append((r, c, v))
                if c >= axis:
                    errs.append("colored source cell is not strictly left of the axis")
                mc = 2 * axis - c
                if not (0 <= mc < w):
                    errs.append("colored source mirror target is out of bounds")
                elif grid[r][mc] != 0:
                    errs.append("colored source mirror target is not initially empty")
    if not colored:
        errs.append("no left-side colored source cells")
    return sorted(set(errs))
