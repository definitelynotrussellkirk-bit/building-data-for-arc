"""Generator for arc_puzzle_bank_21_set23_bundle:hard_p02 — BFS through 2-key maze.

Rule: 4-walled grid. Start (2), goal (3). Color 5 = key1 pickup, color 6 =
door1 (needs key1). Color 7 = key2 pickup, color 8 = door2 (needs key2).
Output paints the BFS path color 9.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_iw,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_start, no_goal, walled_off.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef56ab75c0f3"
VERSION = "3.1.0"  # add executable maze self_check; fix AXES width metadata
TASK_ID = "ef56ab75c0f3"

SUMMARY = (
    "0-bg grid (h~7-9, w~9-11) "
    "with COLOR-4 (yellow) OUTER "
    "WALL BORDER. Interior holds: "
    "(a) ONE COLOR-2 (red) START "
    "cell and ONE COLOR-3 (green) "
    "GOAL cell at Manhattan "
    "distance ≥4; (b) optionally "
    "(use_k1=1) ONE COLOR-5 KEY1 "
    "and ONE COLOR-6 DOOR1; (c) "
    "optionally (use_k2=1) ONE "
    "COLOR-7 KEY2 and ONE COLOR-8 "
    "DOOR2; (d) 0-2 EXTRA INTERIOR "
    "WALL cells (color-4). Rule "
    "(BFS WITH 2-KEY MAZE): "
    "search shortest path from "
    "RED START to GREEN GOAL via "
    "4-conn 0-cells. WALLS (4) "
    "block. DOORS (6, 8) block "
    "UNLESS the matching KEY (5 "
    "or 7) has been picked up "
    "earlier on the path. PAINT "
    "every cell on the shortest "
    "valid path with COLOR 9 "
    "(maroon). Net: 2-key maze "
    "shortest-path traced in "
    "color 9."
)

INVARIANTS = [
    "background is 0; outer border is color-4 walls",
    "interior split into n_doors+1 chambers by solid color-4 walls, each with ONE door cell",
    "the door is the only passage between adjacent chambers, so the path must traverse it",
    "key_i (5/7) sits in a chamber before door_i (6/8); start in chamber 0, goal in the last",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_goal", "walled_off")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_doors":        {"type": "int", "default": "1 easy / 1-2 med / 2 hard", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "rng 4..7", "valid": "3..9"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..7", "valid": "3..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_start|no_goal|walled_off"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n_doors = 1
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 8, 11)
    elif difficulty == "hard":
        n_doors = 2
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 13, 17)
    else:
        n_doors = ctx.draw_int("n_doors", 1, 2)
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 12 if n_doors == 2 else 9, 14)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 4; g[h - 1][c] = 4
    for r in range(h): g[r][0] = 4; g[r][w - 1] = 4

    # vertical wall columns split the interior into n_doors+1 chambers; each
    # wall is solid color-4 except ONE door cell -> the door is the ONLY passage,
    # so the shortest path MUST traverse it (and pick up the matching key first).
    wcols = []
    lo = 3
    for i in range(n_doors):
        hi = (w - 2) - 3 * (n_doors - 1 - i) - 1
        wc = rng.randint(lo, max(lo, hi))
        wcols.append(wc)
        lo = wc + 3
    door_colors = [6, 8][:n_doors]
    key_colors = [5, 7][:n_doors]
    for wc, dcol in zip(wcols, door_colors):
        for r in range(1, h - 1):
            g[r][wc] = 4
        g[rng.randint(1, h - 2)][wc] = dcol      # single door opening

    # chamber column ranges (inclusive interior cols between walls)
    bounds = [1] + [c for wc in wcols for c in (wc - 1, wc + 1)] + [w - 2]
    chambers = [(bounds[2 * i], bounds[2 * i + 1]) for i in range(n_doors + 1)]

    def place_in(c_lo, c_hi, value):
        for _ in range(200):
            r = rng.randint(1, h - 2); c = rng.randint(c_lo, c_hi)
            if g[r][c] == 0:
                g[r][c] = value
                return True
        return False

    place_in(*chambers[0], 2)                     # start in first chamber
    place_in(*chambers[-1], 3)                     # goal in last chamber
    for i in range(n_doors):                       # key_i before door_i (in chamber i)
        place_in(*chambers[i], key_colors[i])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify chambered key-door maze invariants and key-aware reachability."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v not in (0, 2, 3, 4, 5, 6, 7, 8):
                errors.append(f"unexpected color {v} at ({r},{c})")
    for c in range(w):
        if grid[0][c] != 4 or grid[h - 1][c] != 4:
            errors.append("outer border is not all color 4")
            break
    for r in range(h):
        if grid[r][0] != 4 or grid[r][w - 1] != 4:
            errors.append("outer border is not all color 4")
            break

    def cells_of(color):
        return [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]

    starts = cells_of(2)
    goals = cells_of(3)
    if len(starts) != 1:
        errors.append(f"expected exactly one start color 2, found {len(starts)}")
    if len(goals) != 1:
        errors.append(f"expected exactly one goal color 3, found {len(goals)}")

    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errors

    door_cols = []
    for c in range(1, w - 1):
        vals = [grid[r][c] for r in range(1, h - 1)]
        door_cells = [v for v in vals if v in (6, 8)]
        if door_cells or all(v == 4 for v in vals):
            if len(door_cells) == 1 and all(v in (4, door_cells[0]) for v in vals):
                door_cols.append((c, door_cells[0]))
    if not (1 <= len(door_cols) <= 2):
        errors.append(f"expected one or two gated wall columns, found {door_cols}")
    expected = [6, 8][:len(door_cols)]
    actual = [d for _, d in door_cols]
    if actual != expected:
        errors.append(f"door colors left-to-right are {actual}, expected {expected}")

    # Keys must appear in the chamber immediately before their door.
    walls = [c for c, _ in door_cols]
    bounds = [1] + [x for wc in walls for x in (wc - 1, wc + 1)] + [w - 2]
    chambers = [(bounds[2 * i], bounds[2 * i + 1]) for i in range(len(walls) + 1)] if walls else [(1, w - 2)]
    if starts and walls and not (chambers[0][0] <= starts[0][1] <= chambers[0][1]):
        errors.append("start is not in the first chamber")
    if goals and walls and not (chambers[-1][0] <= goals[0][1] <= chambers[-1][1]):
        errors.append("goal is not in the last chamber")
    for idx, key_color in enumerate([5, 7][:len(walls)]):
        key_cells = cells_of(key_color)
        if len(key_cells) != 1:
            errors.append(f"expected exactly one key color {key_color}, found {len(key_cells)}")
            continue
        lo, hi = chambers[idx]
        if not (lo <= key_cells[0][1] <= hi):
            errors.append(f"key color {key_color} is not before its door")

    if starts and goals and not _reachable_with_keys(grid, starts[0], goals[0]):
        errors.append("goal is not reachable under key-door rules")
    return errors


def _reachable_with_keys(grid, start, goal):
    from collections import deque
    h, w = len(grid), len(grid[0])
    key_bit = {5: 1, 7: 2}
    door_need = {6: 1, 8: 2}
    q = deque([(start[0], start[1], 0)])
    seen = {(start[0], start[1], 0)}
    while q:
        r, c, keys = q.popleft()
        if (r, c) == goal:
            return True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            v = grid[nr][nc]
            if v == 4:
                continue
            if v in door_need and not (keys & door_need[v]):
                continue
            nkeys = keys | key_bit.get(v, 0)
            state = (nr, nc, nkeys)
            if state not in seen:
                seen.add(state)
                q.append(state)
    return False


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 4; g[h - 1][c] = 4
    for r in range(h): g[r][0] = 4; g[r][w - 1] = 4
    if name == "no_start":
        # No color-2 start cell — rule has no source to BFS from.
        g[3][3] = 3
        return g
    if name == "no_goal":
        # No color-3 goal cell — rule has no destination.
        g[3][3] = 2
        return g
    if name == "walled_off":
        # Goal isolated by interior walls — no BFS path exists.
        g[3][3] = 2
        g[5][7] = 3
        for c in range(1, w - 1): g[4][c] = 4
        return g
    return g
