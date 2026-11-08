"""Generator for arc_puzzle_bank_21_set11_s:S11_M7.

Rule: the LEGEND is the non-zero values in row 0 (in column order). The
BODY (below row 0) holds color-7 blobs; sort them by (size ascending,
then top-left) and recolor each by the next legend color.

Combinatorial axes: grid size, the legend colors, and the body blobs
(count, distinct sizes, shapes, positions).
Degenerates: no_legend, fewer_legends_than_blobs, equal_size_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "f9787b3cf4de"
VERSION = "2.2.0"  # fix _poly() fallback to preserve requested blob size; add self_check legend/blob invariants
TASK_ID = "f9787b3cf4de"
SUMMARY = (
    "0-bg grid (size varies). Row 0 is a LEGEND of 2-4 distinct colors "
    "(from {1..6,8,9}) in some column order. The BODY (below row 0) has "
    "the same number of color-7 BLOBS of DISTINCT sizes, placed apart. "
    "Rule: sort the blobs by size ascending (tie-break top-left) and "
    "recolor each by the next legend color (smallest blob -> first legend "
    "color). The grid size, legend colors, and blobs' sizes/shapes/"
    "positions all vary freely (was a fixed 3-legend + 3 fixed blobs, ~9 "
    "distinct)."
)

INVARIANTS = [
    "row 0 holds N distinct non-{0,7} legend colors",
    "the body has N non-touching color-7 blobs of DISTINCT sizes",
    "smallest blob maps to the first legend color, etc.",
]

PALETTE_KINDS = ("default", "warm_legend", "cool_legend", "varied_legend")
DEGENERATE_TEXTURES = ("no_legend", "fewer_legends_than_blobs", "equal_size_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

_LEGEND_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)  # non-0 bg, non-7 (blob color)

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm_legend|cool_legend|varied_legend"},
    "n_blobs":        {"type": "int", "default": "varies", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "row_zero_legend", "valid": "row_zero_legend"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..7"},
    "size_spread":    {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm_legend|cool_legend|varied_legend|"
                                "no_legend|fewer_legends_than_blobs|equal_size_blobs"},
}


def _poly(rng, size, maxd):
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
    # Deterministic, connected fallback that preserves the requested size.
    # The old fallback collapsed all size>1 failures to a 2-cell domino, which
    # can violate this task's "distinct blob sizes" invariant.
    cells = [(r, c) for r in range(maxd) for c in range(maxd)]
    if size <= len(cells):
        return cells[:size]
    return cells


def _reserve(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True



def _body_components4(grid, color=7):
    """Return 4-connected components of color in rows 1..h-1."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 1 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify legend/blob invariants for non-degenerate samples."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errs: list[str] = []
    row0 = grid[0]
    legend = [v for v in row0 if v != 0]
    if not legend:
        # Explicitly allow the documented no_legend degenerate texture.
        return errs
    if any(v == 7 for v in legend):
        errs.append("legend row may not contain blob color 7")
    bad_legend = [v for v in legend if v not in _LEGEND_COLORS]
    if bad_legend:
        errs.append(f"legend colors must be in {_LEGEND_COLORS}; found {sorted(set(bad_legend))}")
    if len(legend) != len(set(legend)):
        errs.append("legend colors must be distinct")

    if difficulty == "easy":
        lo, hi = 2, 3
    elif difficulty == "hard":
        lo, hi = 4, 6
    else:
        lo, hi = 3, 5
    if not (lo <= len(legend) <= hi):
        errs.append(f"expected {lo}..{hi} legend entries for difficulty={difficulty!r}; found {len(legend)}")

    body_vals = {grid[r][c] for r in range(1, h) for c in range(w)}
    extra = body_vals - {0, 7}
    if extra:
        errs.append(f"body should contain only 0 background and 7 blobs; found extra colors {sorted(extra)}")

    comps = _body_components4(grid, 7)
    if not comps:
        errs.append("no color-7 body blobs found")
        return errs
    if len(comps) != len(legend):
        errs.append(f"expected one blob per legend entry ({len(legend)}); found {len(comps)} blobs")

    sizes = [len(comp) for comp in comps]
    if len(sizes) != len(set(sizes)):
        errs.append(f"body blob sizes must be distinct; found sizes {sorted(sizes)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nr, md = (8, 11), (11, 14), (2, 3), 3
    elif difficulty == "hard":
        hr, wr, nr, md = (13, 20), (15, 22), (4, 6), 4
    else:
        hr, wr, nr, md = (11, 15), (13, 18), (3, 5), 4

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        n = rng.randint(*nr)
        # N distinct sizes
        sizes = rng.sample(range(1, 10), n)
        legend = rng.sample(_LEGEND_COLORS, n)

        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        for r in range(1):
            for c in range(w):
                occ[0][c] = True   # row 0 reserved for the legend

        # legend in row 0 at distinct columns (column order = legend order)
        cols = sorted(rng.sample(range(w), n))
        for i, c in enumerate(cols):
            g[0][c] = legend[i]

        placed = 0
        for sz in sizes:
            shape = _poly(rng, sz, md)
            bh = max(r for r, c in shape) + 1; bw = max(c for r, c in shape) + 1
            if bh > h - 1 or bw > w:
                continue
            for _t in range(40):
                top = rng.randint(1, h - bh); left = rng.randint(0, w - bw)
                if _reserve(occ, top, left, bh, bw, h, w):
                    for r, c in shape:
                        g[top + r][left + c] = 7
                    placed += 1
                    break
        if placed == n:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_legend":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0), (1, 1)], 7)
        paint_at(g, 5, 3, [(0, 0), (1, 0)], 7)
        return g
    if name == "fewer_legends_than_blobs":
        g[0][0] = 2; g[0][3] = 3
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0), (1, 1)], 7)
        paint_at(g, 5, 3, [(0, 0), (1, 0)], 7)
        paint_at(g, 2, 6, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)], 7)
        return g
    if name == "equal_size_blobs":
        g[0][0] = 2; g[0][3] = 3; g[0][6] = 4
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 7)
        paint_at(g, 5, 3, [(0, 0), (0, 1)], 7)
        paint_at(g, 2, 7, [(0, 0), (0, 1)], 7)
        return g
    return g
