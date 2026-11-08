"""Generator for arc_puzzle_bank_21_set18_bundle:hard_p02 — BFS path with portals.

Rule: BFS from color-2 start to color-3 goal, avoiding color-5 walls. Colors
4 and 6 may form portal pairs (each color appears exactly 2× — entering one teleports
to the other). Path painted color 8 in 0-cells along the route.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_start (no color-2 cell → BFS has no source);
no_goal (no color-3 cell → BFS has no destination); walls_block_path
(color-5 walls fully separate start from goal → no route exists).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "41860bce2569"
VERSION = "2.2.0"  # fix crash/identity: use color-5 walls, paired portals, and keep portals away from endpoints
TASK_ID = "41860bce2569"

SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) with: (a) "
    "ONE COLOR-2 (red) START CELL; (b) ONE "
    "COLOR-3 (green) GOAL CELL ≥4 Manhattan "
    "from start; (c) 0-3 COLOR-8 (cyan) WALL "
    "cells (≥2 cells from start/goal); (d) "
    "optional COLOR-4 PORTAL PAIR (2 cells at "
    "distinct positions, probability 0.5). "
    "Rule: APPLY BFS (4-conn) from RED start "
    "to GREEN goal, avoiding CYAN walls. "
    "COLOR-4/6 PORTAL PAIRS act as teleporters — "
    "entering one portal transports to the "
    "other (zero step). FIND the SHORTEST "
    "PATH. PAINT every 0-cell along that "
    "path with COLOR 8. Start, "
    "goal, walls, and portals stay. Net: "
    "output adds an orange trail of the "
    "shortest portal-aware path."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-2 start cell and one color-3 goal cell",
    "0-3 sparse color-5 wall cells",
    "0-1 optional portal pair (color 4 or 6) with exactly two cells, not adjacent to endpoints",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_goal", "walls_block_path")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "start_goal_with_walls",
                          "valid": "start_goal_with_walls"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_start|no_goal|walls_block_path"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the BFS instance cannot be misread as singleton portals."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    counts = {c: sum(grid[r][cc] == c for r in range(h) for cc in range(w)) for c in range(10)}
    if counts[2] != 1:
        errs.append(f"expected exactly one color-2 start, saw {counts[2]}")
    if counts[3] != 1:
        errs.append(f"expected exactly one color-3 goal, saw {counts[3]}")
    # In the canonical rule every nonzero color except 2/3/5 is interpreted as a portal.
    starts = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    goals = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    start = starts[0] if starts else None
    goal = goals[0] if goals else None
    for color in range(1, 10):
        if color in (2, 3, 5):
            continue
        pts = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if len(pts) not in (0, 2):
            errs.append(f"portal color {color} appears {len(pts)} times, expected 0 or 2")
        if start and goal:
            for p in pts:
                if abs(p[0] - start[0]) + abs(p[1] - start[1]) < 2:
                    errs.append(f"portal color {color} at {p} is adjacent to the start")
                if abs(p[0] - goal[0]) + abs(p[1] - goal[1]) < 2:
                    errs.append(f"portal color {color} at {p} is adjacent to the goal")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        n_walls = ctx.draw_int("n_walls", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n_walls = ctx.draw_int("n_walls", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n_walls = ctx.draw_int("n_walls", 0, 3)
    use_portal = ctx.draw_int("use_portal", 0, 1)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        sr = rng.randint(0, h - 1); sc = rng.randint(0, w - 1)
        g[sr][sc] = 2
        for _ in range(120):
            gr = rng.randint(0, h - 1); gc = rng.randint(0, w - 1)
            if (gr, gc) == (sr, sc): continue
            if abs(gr - sr) + abs(gc - sc) < 4: continue
            g[gr][gc] = 3
            break
        else:
            continue
        for _ in range(n_walls):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0: continue
                if abs(r - sr) + abs(c - sc) < 2: continue
                if abs(r - gr) + abs(c - gc) < 2: continue
                g[r][c] = 5
                break
        if use_portal:
            placed_p = 0
            portal_color = rng.choice([4, 6])
            while placed_p < 2:
                for _t in range(40):
                    r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                    if g[r][c] != 0:
                        continue
                    if abs(r - sr) + abs(c - sc) < 2:
                        continue
                    if abs(r - gr) + abs(c - gc) < 2:
                        continue
                    g[r][c] = portal_color
                    placed_p += 1
                    break
                else:
                    break
        return g
    raise ValueError("could not realize set19 p02 layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_start":
        # No color-2 — BFS has no source.
        g[6][10] = 3
        g[3][5] = 5; g[7][6] = 5
        return g
    if name == "no_goal":
        # No color-3 — BFS has no destination.
        g[2][1] = 2
        g[3][5] = 5; g[7][6] = 5
        return g
    if name == "walls_block_path":
        # Vertical wall fully isolates start from goal.
        g[2][1] = 2; g[6][10] = 3
        for r in range(h):
            g[r][6] = 5
        return g
    return g
