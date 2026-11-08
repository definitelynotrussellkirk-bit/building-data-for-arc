"""Generator for arc_puzzle_bank_21_set14_bundle:hard_n05 — BFS with single key/door.

Rule: start=2, goal=3, walls=5, color 7 = door (need key 6 to pass). Output
paints the shortest path in color 4 (or returns input if unreachable).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: door_without_key (door (7) present but no key (6) → rule's
key-acquired branch never fires, path is blocked at door), no_walls
(no obstacles → BFS reduces to Manhattan distance, no rule branches),
no_path (walls fully encircle goal → rule's "unreachable" branch
fires, output equals input).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd2ddef14b82"
VERSION = "2.1.1"  # avoid normal no-obstacle degenerate; strengthen self_check
TASK_ID = "fd2ddef14b82"

SUMMARY = (
    "0-bg grid (h~8-10, w~10-12) "
    "structured as a small dungeon: "
    "(a) ONE COLOR-2 (red) START cell "
    "at random position; (b) ONE "
    "COLOR-3 (green) GOAL cell at "
    "another position with Manhattan "
    "distance ≥4 from start; (c) "
    "0-4 COLOR-5 (gray) WALL cells "
    "at random empty positions; (d) "
    "0-1 COLOR-6 (magenta) KEY cell; "
    "(e) 0-2 COLOR-7 (orange) DOOR "
    "cells. Rule (BFS PATH WITH "
    "KEY/DOOR): find the SHORTEST "
    "PATH from start to goal using "
    "BFS where WALLS (5) block "
    "movement; DOORS (7) block "
    "UNLESS the KEY (6) has been "
    "picked up earlier on the path. "
    "PAINT every cell on the "
    "shortest path with COLOR 4 "
    "(yellow). If unreachable, "
    "output = input. Start/goal/"
    "key/door/walls stay. Net: BFS "
    "shortest path → yellow trace, "
    "with key→door unlock logic."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-2 start and one color-3 goal cell",
    "0-4 color-5 wall cells",
    "0-1 color-6 key cell, 0-2 color-7 door cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("door_without_key", "no_walls", "no_path")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-10 easy / 9-13 med / 12-18 hard", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "10-12 easy / 11-16 med / 14-22 hard", "valid": "10..24"},
    "n_walls":        {"type": "int", "default": "0-3 easy / 2-8 med / 6-16 hard (reachability-gated)", "valid": "0..18"},
    "use_key":        {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "n_doors":        {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "start_goal_walls_keys_doors",
                       "valid": "start_goal_walls_keys_doors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|door_without_key|no_walls|no_path"},
}


def _reachable(g, h, w):
    """Key/door-aware BFS (mirrors the rule): is the color-3 goal reachable from the
    color-2 start? Walls(5) block; doors(7) block unless a key(6) was collected."""
    from collections import deque
    start = goal = None
    for r in range(h):
        for c in range(w):
            if g[r][c] == 2:
                start = (r, c)
            elif g[r][c] == 3:
                goal = (r, c)
    if start is None or goal is None:
        return False
    seen = {(start[0], start[1], False)}
    dq = deque([(start[0], start[1], False)])
    while dq:
        r, c, k = dq.popleft()
        if (r, c) == goal:
            return True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                v = g[nr][nc]
                if v == 5 or (v == 7 and not k):
                    continue
                ns = (nr, nc, k or v == 6)
                if ns not in seen:
                    seen.add(ns)
                    dq.append(ns)
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        nw_lo, nw_hi, key_hi, door_hi = 1, 3, 0, 0
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 14, 22)
        nw_lo, nw_hi, key_hi, door_hi = 6, 16, 1, 3
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 16)
        nw_lo, nw_hi, key_hi, door_hi = 2, 8, 1, 2
    rng = ctx.draw_rng("layout")

    for _outer in range(60):
        n_walls = rng.randint(nw_lo, nw_hi)
        use_key = rng.randint(0, key_hi)
        n_doors = rng.randint(0, door_hi)
        g = full_grid(h, w, 0)
        sr = rng.randint(0, h - 1); sc = rng.randint(0, w - 1)
        g[sr][sc] = 2
        for _ in range(120):
            gr = rng.randint(0, h - 1); gc = rng.randint(0, w - 1)
            if (gr, gc) == (sr, sc):
                continue
            if abs(gr - sr) + abs(gc - sc) < 4:
                continue
            g[gr][gc] = 3
            break
        else:
            continue
        for _ in range(n_walls):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0:
                    continue
                g[r][c] = 5
                break
        if use_key:
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0:
                    continue
                g[r][c] = 6
                break
        for _ in range(n_doors):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0:
                    continue
                g[r][c] = 7
                break
        # Reachability gate: only accept if the goal is reachable (key/door-aware), so
        # the rule always paints a real shortest path (output != input). Lets us pack
        # many more walls without producing trivial 'unreachable' instances.
        if _reachable(g, h, w):
            return g
    raise ValueError("could not realize a reachable set14 n05 layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "door_without_key":
        # Door (7) present but no key (6) — rule's key-acquired
        # branch never fires; path is blocked at the door.
        g[1][1] = 2
        g[7][9] = 3
        for r in range(2, 7): g[r][5] = 5
        g[4][5] = 7
        return g
    if name == "no_walls":
        # No obstacles — BFS reduces to Manhattan distance; rule's
        # wall-handling branch never fires.
        g[1][1] = 2
        g[7][9] = 3
        return g
    if name == "no_path":
        # Walls fully encircle the goal — rule's "unreachable"
        # branch fires, output equals input.
        g[1][1] = 2
        g[5][5] = 3
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            g[5 + dr][5 + dc] = 5
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the key/door shortest-path dungeon."""
    from collections import Counter
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows have inconsistent widths"]
    counts = Counter(v for row in grid for v in row)
    if counts[2] != 1 or counts[3] != 1:
        errs.append(f"expected exactly one start(2) and goal(3), got start={counts[2]}, goal={counts[3]}")
    if counts[6] > 1:
        errs.append(f"expected at most one key(6), got {counts[6]}")
    if counts[7] > 3:
        errs.append(f"expected at most three doors(7), got {counts[7]}")
    if counts[5] + counts[7] == 0:
        errs.append("normal dungeon should include at least one wall/door obstacle; this leaks the no_walls degenerate")
    starts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    goals = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if starts and goals and abs(starts[0][0] - goals[0][0]) + abs(starts[0][1] - goals[0][1]) < 4:
        errs.append("start and goal should be separated by Manhattan distance >= 4")
    if not _reachable(grid, h, w):
        errs.append("goal should be reachable under the key/door BFS rules")
    return errs
