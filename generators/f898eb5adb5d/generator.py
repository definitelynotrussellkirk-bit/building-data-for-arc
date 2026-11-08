"""Generator for arc_puzzle_bank_21_set24_bundle:hard_p06 — multi-waypoint BFS path.

Rule (re-derived from the canonical solution; the old "avoid 8-walls + 4-portals"
summary was WRONG): BFS from the color-2 start to the color-3 goal over all cells
that are NOT color 5 (color 5 = walls). Cells of colors 4, 6, 7, 9 are WAYPOINTS:
the path must visit them in ASCENDING color order (start -> waypoints sorted by
color -> goal). The intermediate route cells that are currently 0 are painted 8.

v1.1.0 placed color-8 "walls" and color-4 "portals" — but the rule treats 8 and
4 as waypoints and 5 as the wall, so the old inputs mis-modelled it. v2.0.0
matches the real rule: color-5 walls + distinct-color waypoints from {4,6,7,9},
bigger grids, with a Python BFS mirror gating that a full path exists and paints
at least one cell (output != input).

Combinatorial axes: grid size, start/goal positions, wall count, waypoint count.
Degenerates: no_start, no_goal, walls_block_path.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f898eb5adb5d"
VERSION = "2.0.0"  # match the real rule (5=walls, 4/6/7/9=color-ordered waypoints, path painted 8); bigger grids; BFS-gated
TASK_ID = "f898eb5adb5d"

SUMMARY = (
    "0-bg grid (size varies). One color-2 START and one color-3 GOAL, 0-N "
    "color-5 WALL cells (sparse, non-blocking), and 0-3 WAYPOINT cells in "
    "distinct colors from {4,6,7,9}. Rule: BFS over all non-5 cells; the path "
    "must go START -> the waypoints in ASCENDING color order -> GOAL. Paint the "
    "intermediate route cells that are 0 with color 8 (start, goal, walls and "
    "waypoints are preserved). Net: a shortest route threading the waypoints in "
    "order, drawn in color 8. (Was mis-modelled as 8-walls + 4-portals.)"
)

INVARIANTS = [
    "background is 0",
    "exactly one color-2 start and one color-3 goal",
    "walls are color 5 (sparse, do not fully separate start from goal)",
    "waypoints are distinct colors from {4,6,7,9}; the path threads them in color order",
    "a full start->waypoints->goal path exists and paints >=1 cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_goal", "walls_block_path")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "9-11 easy / 11-15 med / 14-20 hard", "valid": "8..22"},
    "grid_w":            {"type": "int", "default": "11-13 easy / 13-18 med / 16-24 hard", "valid": "10..26"},
    "n_walls":           {"type": "int", "default": "0-2 easy / 1-4 med / 2-6 hard", "valid": "0..8"},
    "n_waypoints":       {"type": "int", "default": "0-1 easy / 1-2 med / 2-3 hard", "valid": "0..3"},
    "palette_kind":      {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "2 + walls + waypoints", "valid": "2..6"},
    "position_bias":     {"type": "str", "default": "start_goal_waypoints", "valid": "start_goal_waypoints"},
    "n_distinct_colors": {"type": "int", "default": "up to 6", "valid": "2..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))
_WAYPOINT_COLORS = (4, 6, 7, 9)


def _bfs(g, start, goal):
    """Shortest path over non-5 cells (4-conn); returns list of cells or None."""
    h, w = len(g), len(g[0])
    prev = {start: None}
    dq = deque([start])
    while dq:
        cur = dq.popleft()
        if cur == goal:
            path = []
            while cur is not None:
                path.append(cur); cur = prev[cur]
            return path[::-1]
        for dr, dc in _CARD:
            nb = (cur[0] + dr, cur[1] + dc)
            if (0 <= nb[0] < h and 0 <= nb[1] < w and nb not in prev
                    and g[nb[0]][nb[1]] != 5):
                prev[nb] = cur
                dq.append(nb)
    return None


def _route(g, start, waypoints_sorted, goal):
    """Chain BFS segments start -> waypoints (in order) -> goal."""
    full = [start]
    cur = start
    for tgt in waypoints_sorted + [goal]:
        seg = _bfs(g, cur, tgt)
        if seg is None:
            return None
        full += seg[1:]
        cur = tgt
    return full


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, wl, wpr = (9, 11), (11, 13), (0, 2), (0, 1)
    elif difficulty == "hard":
        hr, wr, wl, wpr = (14, 20), (16, 24), (2, 6), (2, 3)
    else:
        hr, wr, wl, wpr = (11, 15), (13, 18), (1, 4), (1, 2)
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        sr = rng.randint(0, h - 1); sc = rng.randint(0, w - 1)
        g[sr][sc] = 2
        gr = gc = None
        for _ in range(120):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if (r, c) != (sr, sc) and abs(r - sr) + abs(c - sc) >= 4:
                gr, gc = r, c; g[r][c] = 3; break
        if gr is None:
            continue

        free = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        rng.shuffle(free)
        # walls (color 5), not adjacent to start/goal
        n_walls = rng.randint(*wl)
        for (r, c) in list(free):
            if n_walls <= 0:
                break
            if abs(r - sr) + abs(c - sc) < 2 or abs(r - gr) + abs(c - gc) < 2:
                continue
            g[r][c] = 5; free.remove((r, c)); n_walls -= 1
        # waypoints (distinct colors from {4,6,7,9})
        n_wp = rng.randint(*wpr)
        wp_cols = list(_WAYPOINT_COLORS); rng.shuffle(wp_cols)
        wp_cols = wp_cols[:n_wp]
        wps = []
        for col in wp_cols:
            if not free:
                break
            r, c = free.pop()
            g[r][c] = col
            wps.append((col, (r, c)))

        wps_sorted = [p for _, p in sorted(wps)]
        route = _route(g, (sr, sc), wps_sorted, (gr, gc))
        if route is None:
            continue
        painted = [p for p in route[1:-1] if g[p[0]][p[1]] == 0]
        if painted:                         # output != input
            return g

    # deterministic fallback: straight horizontal corridor
    g = full_grid(9, 11, 0)
    g[4][1] = 2; g[4][9] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_start":
        g[6][10] = 3; g[3][5] = 5; g[7][6] = 5
        return g
    if name == "no_goal":
        g[2][1] = 2; g[3][5] = 5; g[7][6] = 5
        return g
    if name == "walls_block_path":
        g[2][1] = 2; g[6][10] = 3
        for r in range(h):
            g[r][6] = 5
        return g
    return g
