"""Generator for arc_additional_puzzle_bank_volume19:H128.

Rule: a unique maze corridor defines the union of all shortest paths
on a blank output.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_corridor, no_endpoints, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c7a8e8d171fa"
VERSION = "2.0.1"
TASK_ID = "c7a8e8d171fa"
SUMMARY = (
    "WALL-BG (color 5) grid (h~7-16, w~8-"
    "18) with: (a) ONE OPEN CORRIDOR of "
    "color-0 cells carved through the "
    "wall in one of 6 SHAPES (straight_"
    "h / straight_v / rect / L / T / "
    "rect_with_branch). The corridor "
    "may have non-trivial geometry "
    "including dead-end branches; (b) "
    "TWO ENDPOINT MARKERS — COLOR 2 "
    "(start) at one corridor end; "
    "COLOR 3 (goal) at the opposite "
    "end. Start and goal are 4-"
    "connectable through the open "
    "corridor (D = shortest-path "
    "distance < ∞). Rule (OUTPUT THE "
    "UNION OF ALL SHORTEST PATHS FROM "
    "START TO GOAL, IN COLOR 8 ON A "
    "FRESH BLANK GRID): RUN BFS from "
    "the COLOR-2 START over 4-conn "
    "non-5 cells to get d_start[r, "
    "c]. RUN BFS from the COLOR-3 "
    "GOAL similarly to get d_goal[r, "
    "c]. Let D = d_start[goal] (the "
    "shortest-path distance). For "
    "EACH cell (r, c): IF d_start[r, "
    "c] + d_goal[r, c] == D, it "
    "lies on SOME shortest path → "
    "PAINT it COLOR 8 (cyan) in the "
    "output. ELSE: output is bg-0. "
    "The walls, original start/goal "
    "colors, and dead-end branches "
    "off the shortest path are "
    "DROPPED. Net: the union of all "
    "shortest paths from start to "
    "goal appears as a cyan blob on "
    "a blank grid."
)

# Rivals: 'output is input' refuted by demos (output is {0,8}).
# 'fill all corridor cells with 8' refuted by demos with a dead-end
# branch in the corridor (the branch stays 0). 'just trace a single
# straight path' refuted by demos with an L-corridor (the output
# covers the whole L, not one line). 'use start color (2)' refuted
# by demos (output uses 8). 'output the entire rectangle bbox of the
# corridor' refuted by demos where the corridor is non-rectangular.
# 4 demos (straight, L-shaped, rectangle, with dead-end branch) pin
# the shortest-path-union semantics.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "walls are color 5",
    "open corridor cells are color 0",
    "exactly one color-2 start cell and one color-3 goal cell, both in the corridor",
    "start and goal are 4-connectable through the corridor (D < infinity)",
    "corridor is non-trivial: ≥3 cells of open space (start, goal, and ≥1 between)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_corridor", "no_endpoints", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 14)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 5)
    # Pick a corridor shape: straight, L-shaped, rectangle, or
    # rectangle-with-dead-end.
    kind = rng.choice(["straight_h", "straight_v", "rect", "L", "T", "rect_with_branch"])
    if kind == "straight_h":
        r = rng.randint(1, h - 2)
        c1 = rng.randint(1, w - 5)
        c2 = rng.randint(c1 + 3, w - 2)
        for c in range(c1, c2 + 1):
            g[r][c] = 0
        g[r][c1] = 2; g[r][c2] = 3
    elif kind == "straight_v":
        c = rng.randint(1, w - 2)
        r1 = rng.randint(1, h - 5)
        r2 = rng.randint(r1 + 3, h - 2)
        for r in range(r1, r2 + 1):
            g[r][c] = 0
        g[r1][c] = 2; g[r2][c] = 3
    elif kind == "rect":
        r1 = rng.randint(1, max(1, h - 5))
        c1 = rng.randint(1, max(1, w - 5))
        r2 = rng.randint(r1 + 2, min(h - 2, r1 + 5))
        c2 = rng.randint(c1 + 2, min(w - 2, c1 + 6))
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                g[r][c] = 0
        # start at one corner, goal at opposite corner
        corner = rng.choice([0, 1, 2, 3])
        if corner == 0:
            g[r1][c1] = 2; g[r2][c2] = 3
        elif corner == 1:
            g[r1][c2] = 2; g[r2][c1] = 3
        elif corner == 2:
            g[r2][c1] = 2; g[r1][c2] = 3
        else:
            g[r2][c2] = 2; g[r1][c1] = 3
    elif kind == "L":
        # Two perpendicular segments meeting at a corner
        r_mid = rng.randint(2, h - 3)
        c_mid = rng.randint(2, w - 3)
        r_end = rng.randint(1, r_mid - 1) if rng.random() < 0.5 else rng.randint(r_mid + 1, h - 2)
        c_end = rng.randint(1, c_mid - 1) if rng.random() < 0.5 else rng.randint(c_mid + 1, w - 2)
        # corner is (r_mid, c_mid); one end at (r_end, c_mid), other at (r_mid, c_end)
        for r in range(min(r_mid, r_end), max(r_mid, r_end) + 1):
            g[r][c_mid] = 0
        for c in range(min(c_mid, c_end), max(c_mid, c_end) + 1):
            g[r_mid][c] = 0
        g[r_end][c_mid] = 2
        g[r_mid][c_end] = 3
    elif kind == "T":
        # T-shape: horizontal bar + vertical descender
        r_bar = rng.randint(1, h - 4)
        c_left = rng.randint(1, w - 6)
        c_right = rng.randint(c_left + 4, w - 2)
        c_drop = rng.randint(c_left + 1, c_right - 1)
        r_bot = rng.randint(r_bar + 2, h - 2)
        for c in range(c_left, c_right + 1):
            g[r_bar][c] = 0
        for r in range(r_bar, r_bot + 1):
            g[r][c_drop] = 0
        # Start at one end of the bar, goal at the bottom of the descender
        g[r_bar][c_left] = 2
        g[r_bot][c_drop] = 3
    else:  # rect_with_branch
        r1 = rng.randint(1, max(1, h - 6))
        c1 = rng.randint(1, max(1, w - 6))
        r2 = rng.randint(r1 + 2, min(h - 3, r1 + 4))
        c2 = rng.randint(c1 + 2, min(w - 3, c1 + 5))
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                g[r][c] = 0
        # Dead-end branch sticking off to one side
        branch_r = rng.randint(r1, r2)
        for c in range(c2 + 1, min(w - 1, c2 + 3)):
            g[branch_r][c] = 0
        g[r1][c1] = 2
        g[r2][c2] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid: walls=5, corridor=0, one color-2 start, one color-3 goal,
    both reachable 4-connected through non-5 cells."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(twos) != 1:
        msgs.append(f"expected exactly 1 color-2 start, found {len(twos)}")
    if len(threes) != 1:
        msgs.append(f"expected exactly 1 color-3 goal, found {len(threes)}")
    if msgs:
        return msgs
    # BFS from start through non-5 cells
    from collections import deque
    sr, sc = twos[0]
    gr_, gc = threes[0]
    visited = set()
    q = deque([(sr, sc)])
    visited.add((sr, sc))
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited and grid[nr][nc] != 5:
                visited.add((nr, nc))
                q.append((nr, nc))
    if (gr_, gc) not in visited:
        msgs.append("start (color-2) cannot reach goal (color-3) through non-5 corridor")
    return msgs


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 5)
    if name == "no_corridor":
        return g
    if name == "no_endpoints":
        for c in range(2, 8):
            g[3][c] = 0
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(10):
                g[r][c] = 0
        return g
    return g
