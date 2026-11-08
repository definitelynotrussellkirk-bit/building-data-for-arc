"""Generator for arc_puzzle_bank_twentysecond21:M150 — pick K-th largest shape via 1-count.

Rule: top-left has K cells of color 1 (K = 1, 2, or 3). Below that:
several shapes in distinct colors and distinct sizes. Output is the
bbox crop of the shape ranked K-th largest.

Combinatorial axes (8): grid_h, grid_w, palette_kind, K,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_K, no_objects, equal_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "fe4b917edd70"
VERSION = "2.1.0"  # retry until at least two placed objects; prevents single-object K-rank demos
TASK_ID = "fe4b917edd70"
SUMMARY = (
    "Row 0 holds K nonzero 'marker' cells (any colors, any "
    "columns) — the rule reads K = the count of nonzero "
    "cells in row 0. Below row 0 are 2-5 connected objects, "
    "each a random polyomino of a DISTINCT size in a "
    "distinct color. Rule: K = nonzero count in row 0; take "
    "everything below row 0, sort those objects by size "
    "DESC (tiebreak top-row then left-col), and OUTPUT the "
    "bbox crop of the K-th largest."
)

INVARIANTS = [
    "background is 0",
    "row 0 holds exactly K nonzero cells (K = the rank to select); rest of row 0 is 0",
    "2-5 connected non-bg objects below row 0, distinct colors and DISTINCT sizes",
    "K is always <= the number of placed objects (so the K-th largest exists)",
    "objects don't touch each other or row 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_K", "no_objects", "equal_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-8 easy / 7-11 med / 9-15 hard", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 9-14 med / 11-18 hard", "valid": "6..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objs":         {"type": "int", "default": "2-3 easy / 3-4 med / 3-5 hard", "valid": "2..5"},
    "K":              {"type": "int", "default": "rng 1..n_placed", "valid": "1..5"},
    "marker_colors":  {"type": "str", "default": "K cells, any nonzero colors (rule counts nonzero)",
                       "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "= n_objs", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "K_marker_row0_objects_below",
                       "valid": "K_marker_row0_objects_below"},
    "n_distinct_colors": {"type": "int", "default": "= n_objs", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, size, max_h, max_w):
    """Random 4-connected polyomino of exactly `size` cells within a max_h x max_w box,
    normalized. Returns None if it can't reach `size`."""
    bh = min(max_h, max(2, size))
    bw = min(max_w, max(2, size))
    cells = {(rng.randrange(bh), rng.randrange(bw))}
    frontier = list(cells)
    while len(cells) < size and frontier:
        cr, cc = rng.choice(frontier)
        opts = [(cr + dr, cc + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= cr + dr < bh and 0 <= cc + dc < bw
                and (cr + dr, cc + dc) not in cells]
        if not opts:
            frontier.remove((cr, cc))
            continue
        nc = rng.choice(opts)
        cells.add(nc)
        frontier.append(nc)
    if len(cells) != size:
        return None
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 11)
        n = ctx.draw_int("n_objs", 2, 3)
        size_hi = 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 15)
        w = ctx.draw_int("grid_w", 11, 18)
        n = ctx.draw_int("n_objs", 3, 5)
        size_hi = 12
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 9, 14)
        n = ctx.draw_int("n_objs", 3, 4)
        size_hi = 9
    rng = ctx.draw_rng("layout")

    # DISTINCT sizes -> unambiguous size rank. Random polyominoes -> the K-th-largest
    # crop varies enormously (was a handful of fixed bank shapes).  Placement can
    # occasionally starve on small canvases, so build a complete teaching instance
    # inside a retry loop instead of returning a one-object rank task.
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        sizes = sorted(rng.sample(range(2, size_hi + 1), min(n, size_hi - 1)), reverse=True)
        palette = list(random_palette(rng, len(sizes)))
        placed: list[tuple[int, int, int, int]] = []
        for size, color in zip(sizes, palette):
            shape = _rand_poly(rng, size, h - 1, w)   # leave row 0 for the marker
            if shape is None:
                continue
            sh = max(c[0] for c in shape) + 1
            sw = max(c[1] for c in shape) + 1
            if sh > h - 1 or sw > w:
                continue
            for _ in range(120):
                r0 = rng.randint(1, h - sh)            # row >= 1 keeps row 0 clear
                c0 = rng.randint(0, w - sw)
                # Include a one-cell halo so objects never touch; touching objects
                # can merge visually and make the size-rank lesson ambiguous.
                bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
                if any(bbox_overlaps(bb, p) for p in placed):
                    continue
                paint_at(g, r0, c0, shape, color)
                placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
                break
        if len(placed) >= 2:
            # K is the rank to pick. Compute it AFTER placement so K <= placed
            # count -> the K-th largest always exists (else list-ref crashes).
            K = rng.randint(1, len(placed))
            # Marker: K nonzero cells in row 0 (any colors, any columns) — the
            # rule only counts nonzero cells in row 0, so color/layout is free.
            marker_cols = rng.sample(range(w), K)
            for c in marker_cols:
                g[0][c] = rng.randint(1, 9)
            return g

    # Deterministic two-object fallback.  This should be practically unreachable,
    # but it preserves the generator's core invariant if a future size band is too
    # tight for the random placer.
    g = full_grid(h, w, 0)
    paint_at(g, 1, 0, [(0, 0), (0, 1), (1, 0)], 4)           # size 3
    paint_at(g, min(h - 1, 4), max(0, w - 2), [(0, 0), (0, 1)], 6)  # size 2
    g[0][0] = 1
    return g


def _components_below_marker(g):
    h, w = len(g), len(g[0])
    seen = set()
    out = []
    for r in range(1, h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            color = g[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and g[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    k = sum(1 for v in grid[0] if v != 0)
    if k <= 0:
        msgs.append("row 0 has no rank marker")
    comps = _components_below_marker(grid)
    if len(comps) < 2:
        msgs.append("fewer than two body objects")
    sizes = [len(cells) for _color, cells in comps]
    if len(set(sizes)) != len(sizes):
        msgs.append("body object sizes are not distinct")
    if k > len(comps):
        msgs.append("rank marker exceeds body object count")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_K":
        # No 1-marker — rule has no rank K to pick.
        paint_at(g, 2, 1, [(0, 0), (0, 1)], 4)
        paint_at(g, 4, 1, [(0, 0), (0, 1), (1, 0)], 5)
        return g
    if name == "no_objects":
        # K marker present but no objects — rule has nothing to rank.
        g[0][0] = 1; g[0][1] = 1
        return g
    if name == "equal_sizes":
        # All objects same size — rank by size is ambiguous.
        g[0][0] = 1; g[0][1] = 1
        paint_at(g, 2, 1, [(0, 0), (0, 1)], 4)
        paint_at(g, 4, 1, [(0, 0), (0, 1)], 5)
        paint_at(g, 4, 5, [(0, 0), (0, 1)], 6)
        return g
    return g
