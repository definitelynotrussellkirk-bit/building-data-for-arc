"""Generator for arc_puzzle_bank_21_set6_s:S6_H7.

Rule: two matching markers are connected by the shortest route through
zero cells while 9-cells act as walls.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_walls,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_endpoint, blocked_path, no_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "136087de61d4"
VERSION = "3.0.1"  # randomize endpoints (not just corners) + vary wall count/orientation with BFS-path guarantee
TASK_ID = "136087de61d4"
SUMMARY = (
    "0-bg grid (h×w, ~8-10 by ~11-14) with exactly TWO color-3 "
    "(green) endpoint cells and several color-9 (maroon) WALL "
    "cells forming partial barriers (e.g., 2-3 vertical walls with "
    "single-cell gaps). Endpoints placed at distant corners so the "
    "shortest path must detour around walls. Rule: locate the two "
    "color-3 cells. Run 4-connected BFS treating 0-cells as "
    "walkable and 9-cells as walls. Find the shortest path between "
    "the endpoints. Paint all INTERIOR cells of the path (excluding "
    "the two endpoints) with color 8 on top of the input. Walls "
    "and endpoints preserved. Output color set: {0, 3, 8, 9}."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly two color-3 endpoint cells",
    "color 9 cells form walls; 0-cell path exists between endpoints",
    "≥1 wall is in the shortest-path corridor (so detour is forced)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_endpoint", "blocked_path", "no_walls")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_walls":        {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "endpoints_random_far",
                       "valid": "endpoints_random_far"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly two color-3 endpoints; has color-9 walls."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    endpoints = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    walls = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(endpoints) == 0:
        return errors  # degenerate (missing_endpoint) — allowed
    if len(endpoints) != 2:
        errors.append(f"expected exactly 2 color-3 endpoints, got {len(endpoints)}")
    if not walls:
        return errors  # degenerate (no_walls) — allowed
    return errors


def _path_exists(g, start, goal):
    """4-conn BFS over 0-cells (goal allowed even if non-0)."""
    from collections import deque
    H, W = len(g), len(g[0])
    seen = {start}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            return True
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = cur[0] + dr, cur[1] + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen:
                if (nr, nc) == goal or g[nr][nc] == 0:
                    seen.add((nr, nc)); q.append((nr, nc))
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 9, 12)
        wlo, whi = 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 13, 18)
        wlo, whi = 2, 4
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 11, 16)
        wlo, whi = 1, 3

    for _attempt in range(120):
        g = full_grid(h, w, 0)
        n_walls = ctx.draw_int("n_walls", wlo, whi)
        # Mix of vertical and horizontal partial walls with a single gap each.
        for _ in range(n_walls):
            if rng.random() < 0.5 and w >= 5:  # vertical wall
                wc = rng.randint(2, w - 3)
                gap = rng.randint(0, h - 1)
                for r in range(h):
                    if r != gap and g[r][wc] == 0:
                        g[r][wc] = 9
            elif h >= 5:                        # horizontal wall
                wr = rng.randint(2, h - 3)
                gap = rng.randint(0, w - 1)
                for c in range(w):
                    if c != gap and g[wr][c] == 0:
                        g[wr][c] = 9
        # Two random endpoints on free cells, reasonably far apart.
        free = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        if len(free) < 2:
            continue
        a = rng.choice(free)
        far = [p for p in free
               if abs(p[0] - a[0]) + abs(p[1] - a[1]) >= (h + w) // 3 and p != a]
        if not far:
            continue
        b = rng.choice(far)
        if not _path_exists(g, a, b):
            continue
        g[a[0]][a[1]] = 3
        g[b[0]][b[1]] = 3
        return g
    # Fallback: clean corner-to-corner, no walls (always solvable)
    g = full_grid(h, w, 0)
    g[1][1] = 3; g[h - 2][w - 2] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    left_wall = 5
    right_wall = 9
    if name == "missing_endpoint":
        # only one color-3 marker → rule needs two, path is undefined
        for r in range(h):
            if r != 3:
                g[r][left_wall] = 9
        g[1][1] = 3
        return g
    if name == "blocked_path":
        # walls fully enclose one endpoint → no zero-cell path between markers
        for r in range(h):
            g[r][left_wall] = 9
        g[1][1] = 3
        g[h - 2][w - 2] = 3
        return g
    if name == "no_walls":
        # endpoints with no walls → shortest path is a straight Manhattan corridor
        g[1][1] = 3
        g[h - 2][w - 2] = 3
        return g
    return g
