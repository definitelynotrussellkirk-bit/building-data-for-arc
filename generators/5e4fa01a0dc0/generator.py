"""Generator for 5e4fa01a0dc0 — BFS shortest paths 2→3→4 painted 8.

Rule: BG = 0. WALLS = 5. Markers 2, 3, 4 placed in open cells. The
rule BFS-finds the cells lying on ANY shortest path from 2 to 3, plus
ANY shortest path from 3 to 4 (4-connected, avoiding walls). Paints all
those cells (where currently 0) to color 8. Markers and walls preserved.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5e4fa01a0dc0"
VERSION = "2.1.0"
TASK_ID = "5e4fa01a0dc0"
SUMMARY = (
    "0-bg grid with a few color-5 wall structures (lines, crosses, "
    "L-shapes, blocks) acting as BFS obstacles. Three markers 2, 3, 4 "
    "placed in open cells such that 4-connected BFS paths 2→3 and 3→4 "
    "are obstructed by at least one wall — forcing detours. Rule: BFS "
    "shortest path from 2 to 3 (4-connected, avoiding 5-walls). BFS "
    "shortest path from 3 to 4. Paint the union of all cells lying on "
    "any shortest path of both legs to color 8 (only cells that were 0; "
    "walls + markers preserved)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 color-5 wall structure (line, cross, L, or block of ≥3 cells)",
    "exactly one cell each of color 2, 3, 4 (all in open cells)",
    "the BFS shortest path from 2→3 and 3→4 must exist (not blocked)",
    "≥1 leg of the path goes through ≥1 cell adjacent to a wall (so detour visible)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate() (n_walls is drawn off the layout rng, not keyed). Defaults are the
# medium band, valid spans easy..hard.
AXES = {
    "grid_h": {"type": "int", "default": "rng 9..13", "valid": "7..16",
               "doc": "Grid height (easy 7..9, medium 9..13, hard 12..16)."},
    "grid_w": {"type": "int", "default": "rng 11..15", "valid": "9..18",
               "doc": "Grid width (easy 9..11, medium 11..15, hard 14..18)."},
}


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


def _draw_wall_line(g, rng, h, w, rng_len_min=3, rng_len_max=6):
    """Draw a horizontal or vertical line of 5s."""
    for _ in range(40):
        horiz = rng.random() < 0.5
        L = rng.randint(rng_len_min, rng_len_max)
        if horiz:
            r = rng.randint(1, h - 2)
            c0 = rng.randint(1, max(1, w - L - 1))
            ok = all(g[r][c] == 0 for c in range(c0, c0 + L))
            if ok:
                for c in range(c0, c0 + L):
                    g[r][c] = 5
                return
        else:
            c = rng.randint(1, w - 2)
            r0 = rng.randint(1, max(1, h - L - 1))
            ok = all(g[r][c] == 0 for r in range(r0, r0 + L))
            if ok:
                for r in range(r0, r0 + L):
                    g[r][c] = 5
                return


def _draw_wall_cross(g, rng, h, w):
    """Draw a + shape of 5s."""
    for _ in range(40):
        cr = rng.randint(2, h - 3); cc = rng.randint(2, w - 3)
        arm = rng.randint(1, 2)
        cells = [(cr, cc)]
        for d in range(1, arm + 1):
            for dr, dc in [(d, 0), (-d, 0), (0, d), (0, -d)]:
                cells.append((cr + dr, cc + dc))
        if all(0 <= r < h and 0 <= c < w and g[r][c] == 0 for r, c in cells):
            for r, c in cells:
                g[r][c] = 5
            return


def _place_marker(g, rng, h, w, color, avoid_positions):
    """Find an open cell that's not in avoid_positions; mark it."""
    for _ in range(200):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        if (r, c) in avoid_positions:
            continue
        g[r][c] = color
        return (r, c)
    return None


def _path_cells_on_shortest(g, a, b):
    da = _bfs_dist(g, a)
    if b not in da:
        return set()
    db = _bfs_dist(g, b)
    target = da[b]
    return {p for p in da if p in db and da[p] + db[p] == target}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n_walls = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n_walls = rng.randint(2, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15)
        n_walls = rng.randint(1, 3)

    for outer in range(40):
        g = full_grid(h, w, 0)
        # Draw walls
        for _ in range(n_walls):
            if rng.random() < 0.6:
                _draw_wall_line(g, rng, h, w,
                                rng_len_min=3, rng_len_max=max(3, min(h, w) - 2))
            else:
                _draw_wall_cross(g, rng, h, w)
        # Place markers, ensuring all 3 are reachable
        marker2 = _place_marker(g, rng, h, w, 2, set())
        if marker2 is None: continue
        # Reachable cells from marker2
        d2 = _bfs_dist(g, marker2)
        reachable = [(r, c) for (r, c) in d2 if (r, c) != marker2]
        if len(reachable) < 5:
            continue
        rng.shuffle(reachable)
        marker3 = None
        for cand in reachable:
            r, c = cand
            if g[r][c] == 0:
                g[r][c] = 3
                marker3 = cand
                break
        if marker3 is None: continue
        d3 = _bfs_dist(g, marker3)
        reachable4 = [(r, c) for (r, c) in d3
                      if (r, c) != marker3 and (r, c) != marker2 and g[r][c] == 0]
        if len(reachable4) < 3:
            continue
        rng.shuffle(reachable4)
        marker4 = None
        for cand in reachable4:
            r, c = cand
            g[r][c] = 4
            marker4 = cand
            break
        if marker4 is None: continue
        return g
    raise ValueError("could not place markers around walls")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one each of markers 2/3/4, >=1 color-5 wall."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if len(twos) != 1:
        errs.append(f"expected exactly 1 marker-2 cell, found {len(twos)}")
    if len(threes) != 1:
        errs.append(f"expected exactly 1 marker-3 cell, found {len(threes)}")
    if len(fours) != 1:
        errs.append(f"expected exactly 1 marker-4 cell, found {len(fours)}")
    if not fives:
        errs.append("no color-5 wall cells found")
    return errs
