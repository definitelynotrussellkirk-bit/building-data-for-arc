"""Generator for arc_puzzle_bank_21_set10_e:hard_j15 — BFS through waypoint with walls.

Rule: BFS from color-2 start to color-3 goal via color-4 waypoint, avoiding
color-5 walls. Output paints the path color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_start, no_waypoint, walls_block_path.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4b9daa75c457"
VERSION = "2.0.1"
TASK_ID = "4b9daa75c457"

SUMMARY = (
    "0-bg grid (h~6-8, w~8-10) with: (a) EXACTLY ONE "
    "color-2 (red) START cell at a random position; "
    "(b) EXACTLY ONE color-4 (yellow) WAYPOINT cell, "
    "Manhattan-distance ≥ 2 from the start; (c) "
    "EXACTLY ONE color-3 (green) GOAL cell, ≥ 2 from "
    "waypoint and ≥ 4 from start; (d) 0-8 color-5 "
    "(gray) WALL cells sprinkled to obstruct simple "
    "paths. Rule: run a 4-connected BFS shortest-path "
    "from START to WAYPOINT through 0-cells (walls and "
    "non-bg block); then from WAYPOINT to GOAL the "
    "same way. CONCATENATE the two path segments. "
    "PAINT every cell on the combined path (excluding "
    "endpoints) with color 8 (cyan). Start, waypoint, "
    "goal, and walls stay. Net: cyan trail from start "
    "→ waypoint → goal, routing around gray walls."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-2 start, one color-4 waypoint, one color-3 goal",
    "0-N color-5 wall cells (some sparse)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_waypoint", "walls_block_path")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "n_walls":        {"type": "int", "default": "rng 2..5", "valid": "0..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "start_waypoint_goal_walls",
                       "valid": "start_waypoint_goal_walls"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 8, 8)
        n_walls = ctx.draw_int("n_walls", 0, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_walls = ctx.draw_int("n_walls", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        n_walls = ctx.draw_int("n_walls", 2, 5)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)

    def place(value):
        for _ in range(80):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = value
            return (r, c)
        return None

    s = place(2)
    if s is None: return g
    wp = None
    for _t in range(80):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0: continue
        if abs(r - s[0]) + abs(c - s[1]) < 2: continue
        g[r][c] = 4; wp = (r, c); break
    gp = None
    for _t in range(120):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0: continue
        if wp and abs(r - wp[0]) + abs(c - wp[1]) < 2: continue
        if abs(r - s[0]) + abs(c - s[1]) < 4: continue
        g[r][c] = 3; gp = (r, c); break
    for _ in range(n_walls):
        for _t in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = 5
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify BFS start/waypoint/goal invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    for color, name in ((2, "start"), (4, "waypoint"), (3, "goal")):
        cnt = flat.count(color)
        if cnt != 1:
            problems.append(f"expected exactly 1 color-{color} {name} cell, found {cnt}")
    return problems


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_start":
        # Waypoint and goal but no start — rule's BFS has no
        # source; path undefined.
        g[2][2] = 4
        g[5][7] = 3
        return g
    if name == "no_waypoint":
        # Start and goal but no waypoint — rule's "via waypoint"
        # constraint has no anchor; path undefined.
        g[1][1] = 2
        g[5][7] = 3
        return g
    if name == "walls_block_path":
        # Walls form a line that disconnects start side from
        # goal side — rule's BFS yields no path.
        g[1][1] = 2
        g[3][4] = 4
        g[5][7] = 3
        for c in range(w): g[2][c] = 5
        return g
    return g
