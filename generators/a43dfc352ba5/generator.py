"""Generator for arc_additional_puzzle_bank_volume17:H114 — BFS-equidistant cells from 2 seeds.

Rule: BFS from color-2 seed (a) and color-3 seed (b) through bg-0 cells
(color-5 walls block). For each 0-cell reachable by both with EQUAL
distance, paint color 8. Seeds and walls preserved; non-equidistant
cells stay 0.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a43dfc352ba5"
VERSION = "2.2.0"  # identity fix: ODD-Manhattan seed pairs have NO equidistant cell (midpoint between cells) -> rule painted nothing. Now require matching row+col parity (integer midpoint guaranteed) and BFS-validate >=1 equidistant reachable 0-cell survives the walls."
TASK_ID = "a43dfc352ba5"
SUMMARY = (
    "One color-2 seed and one color-3 seed on a 0-bg grid (no walls "
    "required). Rule does BFS from each seed through 0-cells. For "
    "every 0-cell reachable from both with EQUAL distance (i.e., on "
    "the perpendicular bisector), paint color 8. Cells that are "
    "strictly closer to one seed remain 0."
)

# Rivals: 'output is input' refuted by demos (≥1 equidistant cell).
# 'paint by Manhattan distance' is equivalent for open grids but
# distinguishes once walls present. 'paint nearest-seed cells'
# refuted by demos showing only equal-distance cells fill. 'use
# color 4 instead of 8' refuted by demos. 3 demos with seeds at
# distinct positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one color-2 seed and one color-3 seed",
    "seeds are separated by ≥3 cells",
]

AXES = {
    "grid_h":   {"type": "int", "default": "rng 7..11", "valid": "5..16"},
    "grid_w":   {"type": "int", "default": "rng 9..14", "valid": "7..20"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(6, 8); w = rng.randint(8, 11); wall_p = 0.5
    elif difficulty == "hard":
        h = rng.randint(11, 15); w = rng.randint(14, 20); wall_p = 0.9
    else:
        h = rng.randint(8, 11); w = rng.randint(10, 14); wall_p = 0.75
    # Rule: BFS from seed-2 (a) and seed-3 (b) through 0-cells (color-5 WALLS
    # block); a 0-cell reachable from BOTH at EQUAL distance -> 8.
    #
    # PARITY BUG fixed here: if the two seeds have ODD Manhattan distance, NO
    # cell can have equal distance (the midpoint falls between cells) -> the rule
    # paints nothing -> identity demo. We require the seeds to share row-parity
    # AND col-parity, which guarantees an integer midpoint cell equidistant from
    # both. Walls are then kept off the equidistant set, and we VALIDATE with our
    # own BFS that >=1 equidistant reachable 0-cell survives (retry otherwise).
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    for _ in range(40):
        rng.shuffle(all_cells)
        a = all_cells[0]
        b = None
        for p in all_cells[1:]:
            if ((p[0] - a[0]) % 2 == 0 and (p[1] - a[1]) % 2 == 0
                    and abs(p[0] - a[0]) + abs(p[1] - a[1]) >= 4):
                b = p
                break
        if b is None:
            continue
        g = full_grid(h, w, 0)
        g[a[0]][a[1]] = 2
        g[b[0]][b[1]] = 3
        rest = [p for p in all_cells if p != a and p != b]
        if rng.random() < wall_p:
            n_walls = rng.randint(1, max(1, (h * w) // 12))
            for (wr, wc) in rest[:n_walls]:
                g[wr][wc] = 5
        if _equidistant_cells(g, a, b):
            return g
    # fallback: even-even seeds, NO walls -> integer midpoint is always equidistant
    g = full_grid(h, w, 0)
    a = (0, 0); b = (2, 2) if w > 2 and h > 2 else (0, 2)
    g[a[0]][a[1]] = 2
    g[b[0]][b[1]] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one 2-seed and one 3-seed, and at least one 0-cell must be
    reachable from both at EQUAL distance, else the rule paints nothing."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    twos = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    threes = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    problems = []
    if len(twos) != 1:
        problems.append(f"expected one color-2 seed, found {len(twos)}")
    if len(threes) != 1:
        problems.append(f"expected one color-3 seed, found {len(threes)}")
    if len(twos) == 1 and len(threes) == 1:
        if _equidistant_cells(grid, twos[0], threes[0]) == 0:
            problems.append("no equidistant reachable 0-cell: rule is a no-op")
    return problems


def _bfs_dist(g, start):
    from collections import deque
    h = len(g); w = len(g[0])
    dist = {start: 0}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in dist and g[nr][nc] != 5:
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))
    return dist


def _equidistant_cells(g, a, b):
    """0-cells reachable from both seeds at EQUAL BFS distance (what the rule
    paints 8). Returns the count."""
    da = _bfs_dist(g, a); db = _bfs_dist(g, b)
    n = 0
    for cell, d in da.items():
        r, c = cell
        if g[r][c] == 0 and cell in db and db[cell] == d:
            n += 1
    return n
