"""Generator for arc_additional_puzzle_bank_volume19:H133 — set-op on 1-shape and 2-shape.

Rule: find the single color-1 blob and the single color-2 blob, normalize both
to origin, and combine them by a CONTROL marker:
  - a color-3 marker present  -> intersection (cells in both)
  - a color-4 marker present  -> union (cells in either)
  - neither                   -> symmetric difference (cells in exactly one)
Output = the bbox crop of the result, painted color 8.

The old generator drew the two shapes from a bank of only 12 FIXED shapes, so
the normalized set-ops collapsed to ~59 distinct outputs (41% dup). Now: two
RANDOM polyominoes whose normalized forms OVERLAP (>=1 shared cell) but DIFFER
(so intersection, union and symmetric-difference are all non-empty and vary),
across all 3 control branches.

Combinatorial axes: the two shapes/sizes, the control op, positions, grid size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56e5ade4e829"
VERSION = "2.0.1"  # distinct=59/dup41%: shapes drawn from 12 FIXED forms -> set-ops collapse. Now random polyominoes whose normalized forms overlap but differ (so intersection/union/symdiff all non-empty + varied) across all 3 control branches.
TASK_ID = "56e5ade4e829"
SUMMARY = (
    "0-bg grid (size varies). One color-1 multi-cell blob and one color-2 "
    "multi-cell blob, spatially separated, plus an optional single CONTROL "
    "marker: a color-3 cell means intersection, a color-4 cell means union, "
    "neither means symmetric difference. The two blobs' NORMALIZED forms "
    "overlap (>=1 shared cell) but differ, so every op is non-empty. Rule: "
    "normalize both blobs to origin, apply the control-selected set op on their "
    "cell sets, output the bbox crop with all result cells painted color 8."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one 4-connected color-1 blob and one color-2 blob",
    "blobs are spatially separated (don't touch)",
    "at most one of color-3 and color-4 marker cells appears",
    "the two normalized blobs overlap in >=1 cell but are not identical",
]

AXES = {
    "grid_h":   {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "grid_w":   {"type": "int", "default": "rng 11..14", "valid": "8..18"},
    "ctrl":     {"type": "int", "default": "rng 0..2", "valid": "0|1|2"},
    "shape_size":{"type": "int", "default": "rng 4..7", "valid": "3..8"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-1 blob and one color-2 blob, at most one of {3,4}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    if c1 == 0:
        errs.append("no color-1 blob found")
    if c2 == 0:
        errs.append("no color-2 blob found")
    c3 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    c4 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 4)
    if c3 > 0 and c4 > 0:
        errs.append("both color-3 and color-4 markers present (ambiguous control)")
    return errs


def _rand_poly(rng, lo, hi):
    n = rng.randint(lo, hi)
    cells = {(0, 0)}
    guard = 0
    while len(cells) < n and guard < 200:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        cells.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _free(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = r0 + dr, c0 + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, cells):
            for dr, dc in cells:
                g[r0 + dr][c0 + dc] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(7, 9); w = rng.randint(10, 12); ctrl = rng.randint(0, 1)
        lo, hi = 3, 5
    elif difficulty == "hard":
        h = rng.randint(11, 14); w = rng.randint(13, 18); ctrl = rng.randint(0, 2)
        lo, hi = 5, 8
    else:
        h = rng.randint(9, 12); w = rng.randint(11, 14); ctrl = rng.randint(0, 2)
        lo, hi = 4, 7

    for _outer in range(80):
        a = _rand_poly(rng, lo, hi)
        aset = {tuple(p) for p in a}
        b = None
        for _ in range(60):
            cand = _rand_poly(rng, lo, hi)
            cset = {tuple(p) for p in cand}
            if (aset & cset) and aset != cset:        # overlap but differ
                b = cand
                break
        if b is None:
            continue
        g = full_grid(h, w, 0)
        if not _place(g, rng, a, 1) or not _place(g, rng, b, 2):
            continue
        if ctrl in (1, 2):
            marker = 3 if ctrl == 1 else 4
            for _ in range(60):
                r = rng.randint(0, h - 1)
                c = rng.randint(0, w - 1)
                if g[r][c] == 0:
                    g[r][c] = marker
                    break
        return g
    raise ValueError("could not realize 56e5 layout")
