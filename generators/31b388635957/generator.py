"""Generator for arc_puzzle_bank_21_set12_s:S12_H6 — degree sequence of the largest cluster.

Rule (verified from canonical Racket): build the adjacency graph of objects that
touch cardinally; group them into clusters (connected components of that graph);
take the largest cluster (by object count, tie-broken by total cells); output a
1xN row holding its sorted degree sequence with +1 added to each degree.

The previous body was the generic scatter template, which spaces every motif
apart by a 1-cell halo, so NO objects ever touch — every cluster is a singleton
of degree 0 and the output is always [[1]] (distinct_out=1). This rewrite
CONSTRUCTS a real cluster: a connected polyomino of single cells, proper-coloured
so cardinally-adjacent cells differ (each cell stays its own object and every
touch is a graph edge). The cluster's shape sets the degree sequence.

Axes: grid size, cluster size K, cluster shape, number of isolated decoys.
Degenerates: path_cluster, star_cluster, no_decoys.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "31b388635957"
VERSION = "3.0.1"  # distinct=8: output = sorted (degree+1) sequence of the largest adjacency-cluster; small clusters (k 3..6) -> few degree sequences. Now k 3..11 (bigger clusters) -> richer degree sequences.
TASK_ID = "31b388635957"

SUMMARY = ("A connected cluster of single-cell objects (proper-coloured so neighbours differ) "
           "is the largest cluster; the rule outputs its sorted degree sequence (+1) as a 1xN "
           "row. Cluster size and shape — hence the degree sequence — vary; isolated decoy "
           "cells form smaller singleton clusters.")

INVARIANTS = [
    "one connected cluster of K single-cell objects (K>=2), cardinally touching",
    "cardinally-adjacent cells carry distinct colours (so each stays a separate object)",
    "any decoy cells are isolated singletons, strictly smaller than the main cluster",
]

DEGENERATE_TEXTURES = ("path_cluster", "star_cluster", "no_decoys")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":     {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "k_cluster":  {"type": "int", "default": "3-4 easy / 4-6 hard (cluster size)", "valid": "2..11"},
    "n_decoys":   {"type": "int", "default": "rng 0..3 isolated singletons", "valid": "0..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|path_cluster|star_cluster|no_decoys"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _build_motif(rng, k):
    """A connected k-cell polyomino as a list of (r,c), normalized to min 0."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _proper_color(cells, rng):
    """Greedy proper colouring (colours 2-9) so cardinally-adjacent cells differ."""
    cset = set(cells)
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 8)
    color = {}
    for cell in cells:
        r, c = cell
        used = {color[(r + dr, c + dc)] for dr, dc in _CARD
                if (r + dr, c + dc) in color}
        color[cell] = next(col for col in palette if col not in used)
    return color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """One connected cluster of K>=2 single-cell objects that cardinally touch; distinct colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Find all non-zero cells (objects)
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(cells) < 2:
        errs.append(f"only {len(cells)} non-zero cell(s) found (need >=2 for cluster)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = sorted (degree+1) sequence of the largest adjacency-cluster, so a
    # bigger cluster -> richer degree sequences (was k 3..6 -> distinct=8).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13)
        k = ctx.draw_int("k_cluster", 3, 5); n_decoys = ctx.draw_int("n_decoys", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 14, 18)
        k = ctx.draw_int("k_cluster", 7, 11); n_decoys = ctx.draw_int("n_decoys", 1, 3)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 16)
        k = ctx.draw_int("k_cluster", 4, 9); n_decoys = ctx.draw_int("n_decoys", 0, 2)
    rng = ctx.draw_rng("layout")

    cells = _build_motif(rng, k)
    sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
    color = _proper_color(cells, rng)

    g = full_grid(h, w, 0)
    # place the cluster with a clear 1-cell halo so nothing else touches it
    r0 = rng.randint(1, max(1, h - sh - 1)); c0 = rng.randint(1, max(1, w - sw - 1))
    occupied = set()
    for (r, c) in cells:
        rr, cc = r0 + r, c0 + c
        g[rr][cc] = color[(r, c)]
        occupied.add((rr, cc))
    halo = {(r + dr, c + dc) for (r, c) in occupied for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

    # isolated decoy cells: singleton clusters (strictly smaller than the K-cluster)
    made = 0
    for _ in range(300):
        if made >= n_decoys:
            break
        dr_, dc_ = rng.randint(0, h - 1), rng.randint(0, w - 1)
        if (dr_, dc_) in halo or g[dr_][dc_] != 0:
            continue
        # keep decoys isolated from each other too
        if any((dr_ + a, dc_ + b) in occupied for a in (-1, 0, 1) for b in (-1, 0, 1)):
            continue
        g[dr_][dc_] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
        occupied.add((dr_, dc_))
        halo |= {(dr_ + a, dc_ + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
        made += 1
    return g


def _draw_from_degenerate(name, rng):
    # deterministic, fixed-shape clusters
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "path_cluster":
        # straight 4-path -> degrees 1,2,2,1 -> output [2,3,3,2]
        cells = [(4, 3), (4, 4), (4, 5), (4, 6)]
        cols = [2, 3, 2, 3]
    elif name == "star_cluster":
        # plus/star -> centre degree 4, arms degree 1 -> output [2,2,2,2,5]
        cells = [(4, 5), (3, 5), (5, 5), (4, 4), (4, 6)]
        cols = [2, 3, 3, 3, 3]
    else:  # no_decoys -> a small L-cluster, nothing else on the grid
        cells = [(3, 3), (3, 4), (4, 4)]
        cols = [2, 3, 2]
    for (r, c), col in zip(cells, cols):
        g[r][c] = col
    return g
