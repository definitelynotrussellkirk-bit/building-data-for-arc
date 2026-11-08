"""Generator for arc_additional_puzzles_21_set20_bundle:M134.

Rule: color-8 cells are PIVOTS. Each non-8 connected blob is rotated 90
degrees clockwise about its NEAREST pivot (Manhattan): a cell at (r,c)
with pivot (pr,pc) -> (pr + (c-pc), pc - (r-pr)). Output is a fresh grid
with the pivots and the rotated blobs.

Combinatorial axes: grid size, the number of pivots, and each pivot's
blob (shape / color / placement near it).
Degenerates: no_pivot, no_blob, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c55491432288"
VERSION = "3.0.0"  # diversity: N random pivots + blobs (shape/color/pos) + grid (was fixed ~9)
TASK_ID = "c55491432288"
SUMMARY = (
    "0-bg grid (size varies) with 1-3 color-8 PIVOTS, each with a nearby "
    "connected BLOB (a distinct color, within Manhattan distance 3 of its "
    "pivot, in its own reserved region so the nearest pivot is "
    "unambiguous and the rotation fits in-bounds). Rule: rotate each blob "
    "90 degrees clockwise about its nearest pivot. The grid size, the "
    "pivot count, and each blob's shape/color/placement all vary freely "
    "(was a fixed 2-pivot layout, ~9 distinct)."
)

INVARIANTS = [
    "1-3 color-8 pivots, each in its own reserved region",
    "each blob is a single connected component of a distinct non-{0,8} color",
    "each blob is nearest to its own pivot and its 90deg-cw rotation is in-bounds",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pivot", "no_blob", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)  # non-0 bg, non-8 pivot

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_pivot|no_blob|full_grid"},
}

_MARGIN = 3  # max Manhattan blob offset; pivot this far from every edge
_MIN_PIVOT_SEP = 7  # if blobs are radius<=3, this makes nearest-pivot strict


def _blob_offsets(rng, size):
    """A connected polyomino of offsets, all within Manhattan 3 of origin,
    none being the origin (the pivot)."""
    for _ in range(80):
        cells = {(0, 1)}   # start adjacent to pivot
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            nc = (r + dr, c + dc)
            if nc != (0, 0) and abs(nc[0]) + abs(nc[1]) <= 3:
                cells.add(nc)
        if (0, 0) not in cells:
            return list(cells)
    return [(0, 1), (1, 1), (-1, 1)]


def _choose_pivots(rng, h, w, n_piv):
    """Choose n pivots with strict nearest-pivot separation for radius-3 blobs.

    The old +/-4 box reservation was too strong for the shipped grid sizes: the
    default path requested 2-3 pivots but almost always returned only one.
    Manhattan separation >=7 is the actual condition needed: every blob cell is
    within distance <=3 of its own pivot, so any other pivot is at distance >=4.
    """
    candidates = [(r, c) for r in range(_MARGIN, h - _MARGIN)
                  for c in range(_MARGIN, w - _MARGIN)]
    for _ in range(120):
        order = candidates[:]
        rng.shuffle(order)
        chosen = []
        for p in order:
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) >= _MIN_PIVOT_SEP
                   for q in chosen):
                chosen.append(p)
                if len(chosen) == n_piv:
                    return chosen
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, npr, szr = (9, 11), (10, 13), (1, 2), (3, 4)
    elif difficulty == "hard":
        hr, wr, npr, szr = (13, 16), (14, 18), (3, 3), (4, 5)
    else:
        hr, wr, npr, szr = (11, 14), (12, 16), (2, 3), (3, 5)

    for _attempt in range(160):
        h = rng.randint(*hr); w = rng.randint(*wr)
        n_piv = rng.randint(*npr)
        pivots = _choose_pivots(rng, h, w, n_piv)
        if len(pivots) != n_piv:
            continue
        g = full_grid(h, w, 0)
        colors = rng.sample(_COLORS, n_piv)
        for (pr, pc), col in zip(pivots, colors):
            offs = _blob_offsets(rng, rng.randint(*szr))
            g[pr][pc] = 8
            for dr, dc in offs:
                g[pr + dr][pc + dc] = col
        return g

    raise ValueError("could not place requested separated pivots/blobs")


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 11, 0)
    if name == "no_pivot":
        g[1][2] = 3
        g[2][1] = 3
        return g
    if name == "no_blob":
        g[2][2] = 8
        g[6][7] = 8
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(11):
                g[r][c] = 8
        return g
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v in (0, 8) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == v):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((v, cells))
    return comps


def _nearest_pivot(cell, pivots):
    dists = [(abs(cell[0] - p[0]) + abs(cell[1] - p[1]), p) for p in pivots]
    dists.sort()
    return dists[0], (dists[1] if len(dists) > 1 else None)


def self_check(grid, *, difficulty=None, meta=None):
    problems = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is not a nonempty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows are ragged"]
    pivots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if difficulty == "hard":
        expected = {3}
    elif difficulty is None:
        expected = {2, 3}
    else:
        expected = {1, 2}
    if len(pivots) not in expected:
        problems.append(f"pivot count {len(pivots)} outside expected {sorted(expected)}")
    if len(pivots) != len(set(pivots)):
        problems.append("duplicate pivot coordinates")
    for pr, pc in pivots:
        if not (_MARGIN <= pr < h - _MARGIN and _MARGIN <= pc < w - _MARGIN):
            problems.append("pivot is too close to an edge for radius-3 rotation")
            break
    for i, p in enumerate(pivots):
        for q in pivots[i + 1:]:
            if abs(p[0] - q[0]) + abs(p[1] - q[1]) < _MIN_PIVOT_SEP:
                problems.append("pivots are too close for strict nearest-pivot assignment")
                break
    comps = _components(grid)
    if pivots and len(comps) != len(pivots):
        problems.append("expected one connected colored blob per pivot")
    colors = [v for v, _ in comps]
    if len(colors) != len(set(colors)):
        problems.append("blob colors should be distinct")
    for _color, cells in comps:
        owners = set()
        for cell in cells:
            (d0, p0), d1 = _nearest_pivot(cell, pivots)
            if d0 > 3:
                problems.append("blob cell is farther than radius 3 from its nearest pivot")
            if d1 is not None and d0 >= d1[0]:
                problems.append("blob cell has ambiguous nearest pivot")
            owners.add(p0)
            rr = p0[0] + (cell[1] - p0[1])
            cc = p0[1] - (cell[0] - p0[0])
            if not (0 <= rr < h and 0 <= cc < w):
                problems.append("90deg rotation would leave the grid")
        if len(owners) != 1:
            problems.append("one blob straddles multiple nearest pivots")
    return sorted(set(problems))
