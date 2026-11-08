"""Generator for c3fb659abfb7 — translate cells by 9-marker vector.

Rule: 2 color-9 markers define a translation vector (sort markers by
cell order; vector = p1 - p0). For every non-0 non-9 cell at (r, c),
paint that cell's color at (r, c) AND at (r+dr, c+dc) on a fresh
canvas. Markers are NOT preserved in output.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c3fb659abfb7"
VERSION = "2.0.1"
TASK_ID = "c3fb659abfb7"
SUMMARY = (
    "0-bg grid (h×w, ~8-12 by ~9-12) with: (a) EXACTLY 2 color-9 "
    "(maroon) MARKER cells at distinct positions defining a "
    "translation vector (the markers are sorted by reading "
    "order, vector = second - first); (b) a connected SHAPE of "
    "2-4 cells in some non-{0, 9} color near one of the markers. "
    "Translated copies must fit in-bounds. Rule: locate the 2 "
    "color-9 markers. Compute (dr, dc) = marker_2 - marker_1. "
    "For each non-0 non-9 cell, paint that cell color at original "
    "position AND at (r+dr, c+dc) on a fresh canvas. Markers do "
    "NOT appear in output."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 color-9 markers at distinct positions",
    "a shape of 2-4 cells in a non-{0, 9} color",
    "translated copies of shape cells stay in bounds",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("single_marker", "no_markers", "no_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "shape_size":     {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "markers_vector",
                       "valid": "markers_vector"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _build_blob(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)

    shape_size = rng.randint(2, 4)
    shape = _build_blob(rng, shape_size)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])

    for _outer in range(60):
        g = full_grid(h, w, 0)
        # Place 2 markers defining a non-trivial vector
        r1 = rng.randint(0, h - 1); c1 = rng.randint(0, w - 1)
        r2 = rng.randint(0, h - 1); c2 = rng.randint(0, w - 1)
        if (r1, c1) == (r2, c2):
            continue
        # Sort markers by cell order to get vector
        m0, m1 = sorted([(r1, c1), (r2, c2)])
        dr = m1[0] - m0[0]
        dc = m1[1] - m0[1]
        if dr == 0 and dc == 0:
            continue
        # Place shape such that both original and translated copy fit
        sr_lo = max(0, -dr)
        sr_hi = h - sh - max(0, dr)
        sc_lo = max(0, -dc)
        sc_hi = w - sw - max(0, dc)
        if sr_hi < sr_lo or sc_hi < sc_lo:
            continue
        sr = rng.randint(sr_lo, sr_hi)
        sc = rng.randint(sc_lo, sc_hi)
        # Place markers and shape, avoiding overlap
        g[r1][c1] = 9
        g[r2][c2] = 9
        bad = False
        cell_positions = [(sr + dr_s, sc + dc_s) for dr_s, dc_s in shape]
        for r, c in cell_positions:
            if g[r][c] == 9:
                bad = True; break
        if bad:
            continue
        for r, c in cell_positions:
            g[r][c] = color
        return g
    raise ValueError("could not place 2 markers + shape with valid vector")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly 2 color-9 markers; >=1 non-{0,9} shape cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nines = sum(grid[r][c] == 9 for r in range(h) for c in range(w))
    if nines != 2:
        errors.append(f"expected exactly 2 color-9 markers, found {nines}")
    shape = sum(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    if shape < 1:
        errors.append("no non-{0,9} shape cells found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "single_marker":
        g[3][4] = 9
        g[5][5] = 2; g[5][6] = 2
        return g
    if name == "no_markers":
        g[3][3] = 2; g[3][4] = 2
        return g
    if name == "no_shape":
        g[2][2] = 9; g[6][7] = 9
        return g
    return g
