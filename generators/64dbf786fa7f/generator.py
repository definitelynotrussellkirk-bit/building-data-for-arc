"""Generator for v1_e_m_h_keys:H3 — translate shapes by the 1->2 marker vector.

REAL rule (verified from canonical Racket): a single COLOR-1 marker cell p1 and
a single COLOR-2 marker cell p2 define a translation vector (p2 - p1). Every
cell whose colour is NOT in {0,1,2} is moved by that vector onto a blank
same-size output (cells shifted out of bounds are dropped). The two markers are
not copied. Output size == input size.

The previous body drew a 6-panel color-9 "find the matching pair" gallery — a
DIFFERENT task. This rewrite builds the real distribution: a 1-marker and a
2-marker defining a vector, plus several other-coloured shapes that get
translated by it.

Degenerates: no_one (no color-1 marker), no_two (no color-2 marker), no_shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "64dbf786fa7f"
VERSION = "3.0.2"  # strengthen self_check: nonzero vector and in-bounds translated shapes
TASK_ID = "64dbf786fa7f"

SUMMARY = (
    "0-bg grid with a single COLOR-1 marker and a single COLOR-2 marker that "
    "define a translation vector (pos2 - pos1), plus several connected SHAPES "
    "in colours from {3..9}. Rule: translate every non-{0,1,2} cell by that "
    "vector onto a blank same-size grid (the markers are dropped). Output size "
    "== input size."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-1 marker and one color-2 marker define the shift vector",
    ">=1 shape in a colour from {3..9}; shapes stay in bounds after the shift",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_one", "no_two", "no_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

_SHAPE_COLORS = [3, 4, 5, 6, 7, 8, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..16", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "8..24"},
    "n_shapes":       {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "vector_plus_shapes",
                       "valid": "vector_plus_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "3..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify markers define a nonzero vector and every shape cell can translate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    shapes = any(grid[r][c] >= 3 for r in range(h) for c in range(w))
    if c1 != 1:
        errs.append(f"expected exactly 1 color-1 marker, found {c1}")
    if c2 != 1:
        errs.append(f"expected exactly 1 color-2 marker, found {c2}")
    if not shapes:
        errs.append("no shape cells (colors >=3) found")
    if c1 == 1 and c2 == 1 and shapes:
        p1 = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 1)
        p2 = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 2)
        dr, dc = p2[0] - p1[0], p2[1] - p1[1]
        if dr == 0 and dc == 0:
            errs.append("color-1 and color-2 markers define a zero translation")
        bad = []
        for r in range(h):
            for c in range(w):
                if grid[r][c] >= 3 and not (0 <= r + dr < h and 0 <= c + dc < w):
                    bad.append((r, c))
        if bad:
            errs.append(f"{len(bad)} shape cells would translate out of bounds")
    return errs


def _rand_poly(rng, maxh, maxw, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    for _ in range(200):
        if len(cells) >= k:
            break
        br, bc = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = br + dr, bc + dc
        if (nr, nc) not in seen and 0 <= nr < maxh and 0 <= nc < maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 8, 11); n = ctx.draw_int("n_shapes", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 22); w = ctx.draw_int("grid_w", 14, 22); n = ctx.draw_int("n_shapes", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 16); w = ctx.draw_int("grid_w", 10, 16); n = ctx.draw_int("n_shapes", 2, 3)
    g = full_grid(h, w, 0)
    # translation vector (nonzero)
    dr = rng.randint(-min(5, h - 2), min(5, h - 2))
    dc = rng.randint(-min(5, w - 2), min(5, w - 2))
    if dr == 0 and dc == 0:
        dc = 1
    # place the 1- and 2-markers realizing the vector
    for _ in range(200):
        r1 = rng.randint(0, h - 1); c1 = rng.randint(0, w - 1)
        r2, c2 = r1 + dr, c1 + dc
        if 0 <= r2 < h and 0 <= c2 < w and (r1, c1) != (r2, c2):
            g[r1][c1] = 1; g[r2][c2] = 2
            break
    else:
        g[0][0] = 1; g[0][1] = 2; dr, dc = 0, 1
    # shapes (colours 3..9) placed so they stay in bounds after the shift
    colors = rng.sample(_SHAPE_COLORS, min(n, len(_SHAPE_COLORS)))
    placed = 0
    for color in colors:
        poly = _rand_poly(rng, rng.randint(1, 4), rng.randint(1, 4), rng.randint(2, 5))
        ph = max(r for r, _ in poly) + 1; pw = max(c for _, c in poly) + 1
        r_lo = max(0, -dr); r_hi = min(h - ph, h - ph - dr)
        c_lo = max(0, -dc); c_hi = min(w - pw, w - pw - dc)
        if r_lo > r_hi or c_lo > c_hi:
            continue
        for _ in range(60):
            r0 = rng.randint(r_lo, r_hi); c0 = rng.randint(c_lo, c_hi)
            cells = [(r0 + a, c0 + b) for a, b in poly]
            if any(g[r][c] != 0 for r, c in cells):
                continue
            for r, c in cells:
                g[r][c] = color
            placed += 1
            break
    if placed == 0:  # guarantee a shape exists to translate
        rr = max(0, -dr); cc = max(0, -dc)
        if g[rr][cc] == 0 and 0 <= rr + dr < h and 0 <= cc + dc < w:
            g[rr][cc] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_one":
        g[3][3] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][6 + dc] = 4
        return g
    if name == "no_two":
        g[3][3] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][6 + dc] = 4
        return g
    if name == "no_shapes":
        g[2][2] = 1; g[4][5] = 2
        return g
    return g
