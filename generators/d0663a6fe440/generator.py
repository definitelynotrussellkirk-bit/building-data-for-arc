"""Generator for arc_additional_puzzle_bank_volume18:H120.

Rule: a unique wall corridor defines the cells lying on every shortest
path.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_corridor, no_endpoints, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d0663a6fe440"
VERSION = "2.0.2"
TASK_ID = "d0663a6fe440"
SUMMARY = (
    "Color-5 (gray) WALL-FILLED grid (h~7-12, "
    "w~8-14) with a CORRIDOR of passable 0-cells "
    "carved through, with one COLOR-2 (red) "
    "START cell at one end and one COLOR-3 "
    "(green) GOAL cell at the other end. Corridor "
    "topology varies: straight horizontal, "
    "straight vertical, L-bend (h-then-v or "
    "v-then-h), or 2-route rectangle PERIMETER "
    "(two equally-short paths around a box). "
    "Passable cells are 0, 2, or 3; walls are 5. "
    "Rule: find ALL SHORTEST PATHS from the red "
    "start to the green goal through passable "
    "cells (4-connectivity, walls 5 block). "
    "Compute the INTERSECTION — every cell "
    "that lies on EVERY shortest path. PAINT "
    "those cells with COLOR 8 (cyan). Red "
    "start and green goal stay. For "
    "single-corridor topologies the whole path "
    "becomes cyan; for rectangle-perimeter "
    "topology only the start/goal corners "
    "(intersection cells) get painted. Net: "
    "intersection of all shortest paths "
    "highlighted in cyan."
)

# Rivals: 'paint any shortest path cell' refuted by ≥1 demo where
# multiple shortest paths exist and only intersection cells are
# painted. 'paint just endpoints' refuted by any demo with painted
# interior. 'use red/green for paint' refuted by any demo (paint is 8).
# 'paint all passable cells' refuted by ≥1 demo where some passable
# cells are off all shortest paths.
# 4 demos with varied corridor shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "walls are 5",
    "passable cells are 0, 2, or 3",
    "there is exactly one red start and one green goal",
    "start and goal are connected through passable cells; some boards have multiple equal shortest routes",
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify walls, endpoints, and start-goal passable connectivity."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    bad = sorted({grid[r][c] for r in range(h) for c in range(w)} - {0, 2, 3, 5})
    if bad:
        errs.append(f"unexpected colors in corridor grid: {bad}")
    if not any(grid[r][c] == 5 for r in range(h) for c in range(w)):
        errs.append("no color-5 wall cells found")
    starts = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    goals = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(starts) != 1:
        errs.append(f"expected exactly one color-2 start, found {len(starts)}")
    if len(goals) != 1:
        errs.append(f"expected exactly one color-3 goal, found {len(goals)}")
    if errs or not starts or not goals:
        return errs
    start, goal = starts[0], goals[0]
    stack = [start]
    seen = {start}
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in seen and grid[rr][cc] in (0, 2, 3):
                seen.add((rr, cc))
                stack.append((rr, cc))
    if goal not in seen:
        errs.append("start and goal are not connected through passable cells")
    if len(seen) < 4:
        errs.append("corridor is too short to demonstrate shortest-path behavior")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 20)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 14)
    g = full_grid(h, w, 5)
    # Pick a corridor topology with optional branches that share some
    # cells but diverge in others — so the rule's intersection has
    # variety. Otherwise output is the whole corridor (degenerate
    # case for this rule).
    orientation = rng.choice(["horizontal", "vertical", "h_then_v",
                              "v_then_h", "two_route"])
    if orientation == "horizontal":
        r1 = rng.randint(1, h - 2)
        c1 = rng.randint(1, w - 5)
        c2 = rng.randint(c1 + 3, w - 2)
        for c in range(c1, c2 + 1):
            g[r1][c] = 0
        g[r1][c1] = 2; g[r1][c2] = 3
    elif orientation == "vertical":
        c1 = rng.randint(1, w - 2)
        r1 = rng.randint(1, h - 5)
        r2 = rng.randint(r1 + 3, h - 2)
        for r in range(r1, r2 + 1):
            g[r][c1] = 0
        g[r1][c1] = 2; g[r2][c1] = 3
    elif orientation == "h_then_v":
        r1 = rng.randint(1, h - 4)
        c1 = rng.randint(1, w - 4)
        c2 = rng.randint(c1 + 2, w - 2)
        r2 = rng.randint(r1 + 2, h - 2)
        for c in range(c1, c2 + 1):
            g[r1][c] = 0
        for r in range(r1, r2 + 1):
            g[r][c2] = 0
        g[r1][c1] = 2; g[r2][c2] = 3
    elif orientation == "v_then_h":
        r1 = rng.randint(1, h - 4)
        c1 = rng.randint(1, w - 4)
        r2 = rng.randint(r1 + 2, h - 2)
        c2 = rng.randint(c1 + 2, w - 2)
        for r in range(r1, r2 + 1):
            g[r][c1] = 0
        for c in range(c1, c2 + 1):
            g[r2][c] = 0
        g[r1][c1] = 2; g[r2][c2] = 3
    else:  # two_route: rectangle perimeter — multiple shortest paths,
           # only the corners are on every shortest path
        if h < 6 or w < 6:
            # fallback to simple
            r1 = rng.randint(1, h - 2)
            c1 = rng.randint(1, w - 5)
            c2 = rng.randint(c1 + 3, w - 2)
            for c in range(c1, c2 + 1):
                g[r1][c] = 0
            g[r1][c1] = 2; g[r1][c2] = 3
        else:
            r1 = rng.randint(1, h - 5)
            r2 = rng.randint(r1 + 3, h - 2)
            c1 = rng.randint(1, w - 5)
            c2 = rng.randint(c1 + 3, w - 2)
            for c in range(c1, c2 + 1):
                g[r1][c] = 0
                g[r2][c] = 0
            for r in range(r1, r2 + 1):
                g[r][c1] = 0
                g[r][c2] = 0
            g[r1][c1] = 2; g[r2][c2] = 3
    return g


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
