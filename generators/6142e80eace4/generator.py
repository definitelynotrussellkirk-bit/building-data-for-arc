"""Generator for arc_puzzle_bank_21_set10_e:hard_j18.

Rule: sort blobs by left-column; for consecutive pairs, draw an L-path of
8s (horizontal along the first anchor's row, then vertical along the
second anchor's column) connecting their top-left corners.

Combinatorial axes: grid size, the number of blobs, their shapes / colors
/ positions (distinct left-columns so the sort is unambiguous).
Degenerates: only_one_blob, blobs_aligned_col, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "6142e80eace4"
VERSION = "2.1.0"  # diversity: random N blobs (shape/color/pos, distinct cols) + grid (was 3 fixed blobs)
TASK_ID = "6142e80eace4"
SUMMARY = (
    "0-bg grid (size varies). 3-4 distinct-color BLOBS (random small "
    "shapes) at DISTINCT left-columns, placed apart. Rule: sort the blobs "
    "by their leftmost column and, for each consecutive pair, draw an "
    "L-PATH of COLOR 8 (cyan) — horizontal along the first blob's "
    "top-row to the second's column, then vertical to the second's "
    "top-left — connecting their top-left corners. The grid size, the "
    "number of blobs, their shapes / colors / positions all vary freely, "
    "so the connecting path (the output) varies too (was 3 fixed blobs)."
)

INVARIANTS = [
    "3-4 non-touching blobs of at least two cells at distinct left-columns",
    "the sort-by-column order is unambiguous",
    "L-paths of 8 connect consecutive top-left anchors",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("only_one_blob", "blobs_aligned_col", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "13..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|rainbow"},
    "num_blobs":      {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "blob_size":      {"type": "str", "default": "varied", "valid": "varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|rainbow|only_one_blob|blobs_aligned_col|no_blobs"},
}


def _random_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in norm) < maxd and max(c for r, c in norm) < maxd:
            return norm
    return [(0, 0), (0, 1)]


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nbl = (8, 10), (13, 14), 3
    elif difficulty == "hard":
        hr, wr, nbl = (10, 16), (15, 18), 4
    else:
        hr, wr, nbl = (8, 12), (13, 16), rng.randint(3, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], nbl)
        anchors_c = set()
        ok = True
        for i in range(nbl):
            b = _random_poly(rng, rng.randint(2, 4), 3)
            bh = max(r for r, c in b) + 1; bw = max(c for r, c in b) + 1
            placed = False
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if left in anchors_c:                # distinct left-columns
                    continue
                if _free(occ, b, top, left, h, w):
                    for r, c in b:
                        g[top + r][left + c] = colors[i]; occ[top + r][left + c] = True
                    anchors_c.add(left)
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if ok:
            return g

    return g   # fallback (rare)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    comps = _components(grid)
    if len(comps) not in (3, 4):
        errs.append(f"expected 3-4 blobs, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("blob colors must be distinct so objects remain separable")
    if 8 in colors:
        errs.append("input blob uses path color 8")
    lefts = [min(c for _, c in cells) for _, cells in comps]
    if len(lefts) != len(set(lefts)):
        errs.append("left-column sort order is ambiguous")
    for color, cells in comps:
        if len(cells) < 2:
            errs.append("blob has only one cell, so the path can erase the entire object")
            break
    all_cells = []
    for i, (_, cells) in enumerate(comps):
        all_cells.extend((cell, i) for cell in cells)
    occupied = {cell: i for cell, i in all_cells}
    for (r, c), i in all_cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                j = occupied.get((r + dr, c + dc))
                if j is not None and j != i:
                    errs.append("blobs touch/diagonal-touch; object separation is unclear")
                    return errs
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    if name == "only_one_blob":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0), (1, 1)], 2)
        return g
    if name == "blobs_aligned_col":
        paint_at(g, 1, 5, [(0, 0), (0, 1), (1, 0)], 2)
        paint_at(g, 4, 5, [(0, 0), (0, 1), (1, 0)], 4)
        paint_at(g, 7, 5, [(0, 0), (0, 1)], 7)
        return g
    if name == "no_blobs":
        return g
    return g
