"""Generator for additional_scaffolded:H7.

Rule: take the color-6 object sizes, sort descending, and draw them as a
BAR on the color-2 marker's row — each size is a run of `size` color-3
cells, runs separated by a single gap, starting just right of the marker.

Combinatorial axes: grid size, the color-6 objects (count + distinct
sizes + positions), and the marker position.
Degenerates: no_objects, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "1165179c0d2e"
VERSION = "2.0.1"  # +self_check
TASK_ID = "1165179c0d2e"
SUMMARY = (
    "0-bg grid (size varies). 2-5 color-6 (magenta) OBJECTS of DISTINCT "
    "sizes (single connected components, placed apart, all above the "
    "marker row), and a color-2 (red) MARKER on the bottom row with blank "
    "space to its right. Rule: sort the object sizes descending and draw "
    "a BAR on the marker's row — each size = a run of that many color-3 "
    "(green) cells, runs separated by one gap, starting right of the "
    "marker. The grid size, object count/sizes/positions and marker "
    "column all vary freely (was 3 fixed objects, ~11 distinct)."
)

INVARIANTS = [
    "2-5 separated color-6 objects of distinct sizes, all above the marker row",
    "one color-2 marker on a row clear to its right (room for the bar)",
    "sum(sizes) + (n-1) gaps fits in the row to the right of the marker",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "no_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "15..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_objects|no_marker|full_grid"},
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
    return [(0, 0)] if size == 1 else [(0, 0), (0, 1)]


def _reserve(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nr = (8, 10), (15, 18), (2, 3)
    elif difficulty == "hard":
        hr, wr, nr = (10, 14), (19, 26), (3, 5)
    else:
        hr, wr, nr = (9, 12), (16, 22), (3, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        n = rng.randint(*nr)
        # distinct sizes whose bar (sum + n-1 gaps) fits to the right of col 0
        budget = w - 1 - (n - 1)        # cells available for 3-runs (marker at col 0)
        if budget < n:                  # need >=1 per object
            continue
        sizes = None
        for _t in range(30):
            cand = rng.sample(range(1, min(7, budget) + 1), n) if min(7, budget) >= n else None
            if cand and sum(cand) <= budget:
                sizes = cand; break
        if sizes is None:
            continue

        mr = h - 1
        g = full_grid(h, w, 0)
        g[mr][0] = 2
        occ = [[False] * w for _ in range(h)]
        for c in range(w):
            occ[mr][c] = True          # keep the marker/bar row clear of objects
        placed = 0
        for sz in sizes:
            shape = _conn_poly(rng, sz, 3)
            bh = max(r for r, c in shape) + 1; bw = max(c for r, c in shape) + 1
            if bh > mr or bw > w:
                continue
            for _t in range(40):
                top = rng.randint(0, mr - bh); left = rng.randint(0, w - bw)
                if _reserve(occ, top, left, bh, bw, h, w):
                    for r, c in shape:
                        g[top + r][left + c] = 6
                    placed += 1
                    break
        if placed == n:
            return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one color-6 object cell AND one color-2 marker cell present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    h, w = len(grid), len(grid[0])
    has_obj = any(grid[r][c] == 6 for r in range(h) for c in range(w))
    has_marker = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_obj:
        errors.append("no color-6 object cells found")
    if not has_marker:
        errors.append("no color-2 marker cell found")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 16, 0)
    if name == "no_objects":
        g[7][0] = 2
        return g
    if name == "no_marker":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0), (1, 1)], 6)
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(16):
                g[r][c] = 6
        return g
    return g
