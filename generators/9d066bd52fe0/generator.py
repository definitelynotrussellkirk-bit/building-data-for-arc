"""Generator for arc_puzzle_bank_21_set8:hard_h17.

Creates small geodesic Voronoi scenes: singleton colored seeds compete
through black space while gray walls block orthogonal movement.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d066bd52fe0"
VERSION = "2.0.1"
TASK_ID = "9d066bd52fe0"

SUMMARY = (
    "0-bg grid (h~7-9, w~"
    "8-11) with: (a) 1-2 "
    "GRAY (COLOR-5) WALLS — "
    "each wall is a near-"
    "full row or column "
    "with 1-2 GAPS (openings) "
    "at random positions; "
    "(b) 2-3 SINGLETON SEED "
    "CELLS in DISTINCT "
    "colors from {2, 3, 4, "
    "6, 7, 8, 9} placed at "
    "BG positions with "
    "Manhattan distance ≥ "
    "max(3, min(h, w)//2) "
    "between any pair. Rule "
    "(GEODESIC VORONOI FILL "
    "AROUND GRAY WALLS): "
    "For EACH BG cell at "
    "(r, c): compute "
    "GEODESIC (4-conn, "
    "non-wall) distance to "
    "EACH SEED. PAINT the "
    "cell with the COLOR of "
    "the NEAREST seed by "
    "geodesic distance. "
    "Ties broken task-"
    "specific. Walls stay 5. "
    "Net: each connected "
    "region partitions by "
    "nearest seed (geodesic "
    "Voronoi), with walls "
    "blocking shortest "
    "paths."
)

INVARIANTS = [
    "background is 0",
    "gray 5 cells are walls",
    "all non-wall colors are singleton seeds",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "rng 8..11", "valid": "7..13"},
    "n_seeds": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "n_walls": {"type": "int", "default": "rng 1..2", "valid": "0..3"},
}


def _zero_cells(g):
    return [
        (r, c)
        for r, row in enumerate(g)
        for c, value in enumerate(row)
        if value == 0
    ]


def _add_wall(g, rng):
    h, w = len(g), len(g[0])
    vertical = rng.choice([True, False])
    if vertical and w >= 5:
        c = rng.randint(2, w - 3)
        gap_count = 1 if h <= 7 else rng.randint(1, 2)
        gaps = set(rng.sample(range(h), gap_count))
        for r in range(h):
            if r not in gaps:
                g[r][c] = 5
    elif h >= 5:
        r = rng.randint(2, h - 3)
        gap_count = 1 if w <= 8 else rng.randint(1, 2)
        gaps = set(rng.sample(range(w), gap_count))
        for c in range(w):
            if c not in gaps:
                g[r][c] = 5


def _far_enough(pos, chosen, min_gap):
    r, c = pos
    return all(abs(r - rr) + abs(c - cc) >= min_gap for rr, cc in chosen)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = ctx.draw_int("grid_h", 7, 9)
    w = ctx.draw_int("grid_w", 8, 11)
    n_seeds = ctx.draw_int("n_seeds", 2, 3)
    n_walls = ctx.draw_int("n_walls", 1, 2)
    rng = ctx.draw_rng("layout")

    for _ in range(60):
        g = full_grid(h, w, 0)
        for _ in range(n_walls):
            _add_wall(g, rng)

        cells = _zero_cells(g)
        rng.shuffle(cells)
        chosen = []
        min_gap = max(3, min(h, w) // 2)
        for pos in cells:
            if _far_enough(pos, chosen, min_gap):
                chosen.append(pos)
                if len(chosen) == n_seeds:
                    break
        if len(chosen) < n_seeds:
            continue

        colors = rng.sample([2, 3, 4, 6, 7, 8, 9], n_seeds)
        for (r, c), color in zip(chosen, colors):
            g[r][c] = color
        return g

    raise ValueError("could not place geodesic seeds")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0; color-5 wall cells present; non-{0,5} cells are isolated singletons."""
    msgs = []
    h, w = len(grid), len(grid[0])
    count_5 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    if count_5 == 0:
        msgs.append("no color-5 wall cells found")
    # Every non-{0,5} value should appear exactly once (singleton seed)
    from collections import Counter
    color_counts = Counter(grid[r][c] for r in range(h) for c in range(w)
                           if grid[r][c] not in (0, 5))
    multi = {c: n for c, n in color_counts.items() if n > 1}
    if multi:
        msgs.append(f"non-singleton seed colors: {multi}")
    if not color_counts:
        msgs.append("no seed cells (non-{0,5}) found")
    return msgs
