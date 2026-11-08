"""Generator for arc_puzzle_bank_21_next:hard_c07 — Pick n-th largest object.

Rule: n = count of 9s in row 0. Zero out the row-0 9s, then sort the body
objects by size descending (tie-break by position) and output the bbox crop of
the n-th object (index n-1).

The old generator placed only THREE FIXED motifs (sizes 4/3/2) so the n-th
largest was always one of three shapes -> distinct=21, out=2. Now: K (3-6)
RANDOM polyominoes of DISTINCT sizes (so the ranking is unambiguous), distinct
colors, scattered; n = a random count of row-0 9s in [1, K]. The chosen object
(and thus the output shape/size) varies widely.

Combinatorial axes: object count K, each object's size/shape, n (row-0 9 count
-> which rank is selected), colors, positions, grid size.
Degenerates: no_nines, single_object, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "532f4a848b71"
VERSION = "3.0.1"
TASK_ID = "532f4a848b71"
SUMMARY = (
    "0-bg grid (size varies). Row 0 holds n color-9 markers (n in [1, K]). The "
    "body (rows 1+) holds K (3-6) connected objects of DISTINCT sizes in "
    "distinct non-{0,9} colors at scattered, separated positions. Rule: n = "
    "count of row-0 9s; zero them; sort body objects by size descending "
    "(tie-break by position); output the bbox crop of the n-th object. The "
    "selected object (output shape/size/color) varies with n, the object sizes "
    "and shapes."
)

INVARIANTS = [
    "row 0 contains between 1 and K color-9 markers",
    "the body holds K connected objects of distinct sizes",
    "objects are separated and in distinct non-{0,9} colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_nines", "single_object", "all_same_size")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..18"},
    "n_objects":      {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "n_nines":        {"type": "int", "default": "rng 1..K", "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, n):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (1 <= rr < h and 0 <= cc < w):     # keep body in rows >= 1
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; row 0 has ≥1 color-9 marker; body has non-bg objects."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nines_row0 = [c for c in range(w) if grid[0][c] == 9]
    if not nines_row0:
        return errors  # degenerate (no_nines) — allowed
    body_cells = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if not body_cells:
        errors.append("no body objects found in rows 1+")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 9, 12); k = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 14, 18)
        k = rng.randint(5, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 15)
        k = rng.randint(4, 5)

    sizes = sorted(rng.sample(range(1, 9), k), reverse=True)   # distinct sizes
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], k)
    g = full_grid(h, w, 0)
    placed = 0
    for sz, col in zip(sizes, colors):
        cells = _poly(rng, sz)
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        for _ in range(150):
            top = rng.randint(1, h - sh)
            left = rng.randint(0, w - sw)
            if _free(g, top, left, cells):
                paint_at(g, top, left, cells, col)
                placed += 1
                break
    n = min(rng.randint(1, k), max(1, placed))
    ncols = [c for c in range(w)]
    rng.shuffle(ncols)
    for c in ncols[:n]:
        g[0][c] = 9
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 11, 0)
    if name == "no_nines":
        paint_at(g, 2, 2, [(0, 0), (0, 1), (1, 0)], 3)
        return g
    if name == "single_object":
        g[0][2] = 9
        paint_at(g, 3, 3, [(0, 0), (0, 1), (1, 1)], 4)
        return g
    if name == "all_same_size":
        g[0][1] = 9
        paint_at(g, 2, 1, [(0, 0), (0, 1)], 2)
        paint_at(g, 5, 6, [(0, 0), (0, 1)], 3)
        return g
    return g
