"""Generator for 561ebfa521f0 — BFS path union 2→4→3 painted 8.

Rule: BFS shortest path from red(2) → yellow(4), union with BFS from
yellow(4) → green(3). Cells lying on any shortest path of both legs
are painted color 8 (only if they were 0). Walls (5), markers, and
non-path bg preserved.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "561ebfa521f0"
# 2.1.0: defect-lint identity_demo — the three markers could land ADJACENT (BFS
# distance 1), leaving no intermediate path cells to paint (output == input).
# Marker picks now require BFS distance >= 3 between every pair.
VERSION = "2.1.0"
TASK_ID = "561ebfa521f0"
SUMMARY = (
    "Grid with color-5 BORDER (outer ring of walls). Interior is mostly "
    "0-bg with a few scattered 5-walls forming obstacles. Three "
    "markers: color-2 (red), color-4 (yellow), color-3 (green) placed "
    "at distinct interior positions, all reachable from each other "
    "through non-wall cells. Rule: BFS shortest path 2→4 (union of "
    "all shortest paths). BFS 4→3. Paint cells on either leg's union "
    "with color 8 (only cells that are currently 0). Walls and "
    "markers preserved."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "outer border is color-5 wall ring",
    "interior 0-bg with 1-6 additional scattered color-5 walls",
    "exactly one each of color-2, color-3, color-4 markers in the interior",
    "all 3 markers reachable from each other (path through non-walls exists)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard.
AXES = {
    "grid_h":  {"type": "int", "default": "rng 9..12", "valid": "7..16",
                "doc": "Grid height (easy 7..9, medium 9..12, hard 11..16)."},
    "grid_w":  {"type": "int", "default": "rng 11..14", "valid": "9..18",
                "doc": "Grid width (easy 9..11, medium 11..14, hard 13..18)."},
    "n_walls": {"type": "int", "default": "rng 2..5", "valid": "1..8",
                "doc": "Interior scattered walls (easy 1..3, medium 2..5, hard 4..8)."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: outer border is color-5, exactly one each of color 2, 3, 4 inside."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    # Outer border must be all 5s
    border_ok = all(
        grid[0][c] == 5 and grid[h - 1][c] == 5 for c in range(w)
    ) and all(
        grid[r][0] == 5 and grid[r][w - 1] == 5 for r in range(h)
    )
    if not border_ok:
        errs.append("outer border is not all color-5")
    # Count markers
    for color in (2, 3, 4):
        count = sum(1 for r in range(1, h - 1) for c in range(1, w - 1)
                    if grid[r][c] == color)
        if count != 1:
            errs.append(f"expected exactly 1 color-{color} marker, found {count}")
    return errs


def _bfs_dist(g, start):
    h, w = len(g), len(g[0])
    dist = {start: 0}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if g[nr][nc] == 5:
                continue
            if (nr, nc) in dist:
                continue
            dist[(nr, nc)] = dist[(r, c)] + 1
            q.append((nr, nc))
    return dist


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n_walls = ctx.draw_int("n_walls", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        n_walls = ctx.draw_int("n_walls", 4, 8)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        n_walls = ctx.draw_int("n_walls", 2, 5)

    for outer in range(40):
        g = full_grid(h, w, 0)
        # Border walls
        for c in range(w):
            g[0][c] = 5
            g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5
            g[r][w - 1] = 5
        # Interior walls
        for _ in range(n_walls):
            for _ in range(30):
                wr = rng.randint(2, h - 3); wc = rng.randint(2, w - 3)
                if g[wr][wc] == 0:
                    g[wr][wc] = 5
                    break
        # Place markers
        m2 = m4 = m3 = None
        for _ in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] == 0:
                g[r][c] = 2; m2 = (r, c); break
        if m2 is None: continue
        d2 = _bfs_dist(g, m2)
        # BFS distance >= 3 between markers: adjacent markers leave no
        # intermediate path cells for the rule to paint (identity demo).
        reachable = [p for p in d2 if d2[p] >= 3]
        if len(reachable) < 4:
            continue
        rng.shuffle(reachable)
        for cand in reachable:
            r, c = cand
            if g[r][c] == 0:
                g[r][c] = 4; m4 = cand; break
        if m4 is None: continue
        d4 = _bfs_dist(g, m4)
        reachable4 = [p for p in d4
                      if d4[p] >= 3 and d2.get(p, 0) >= 3 and g[p[0]][p[1]] == 0]
        if len(reachable4) < 2:
            continue
        rng.shuffle(reachable4)
        for cand in reachable4:
            r, c = cand
            g[r][c] = 3; m3 = cand; break
        if m3 is None: continue
        return g
    raise ValueError("could not realize 3-marker corridor")
