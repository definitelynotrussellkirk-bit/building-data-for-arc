"""Generator for arc_additional_puzzle_bank_volume19:M131 — Shortest-path fill in a maze.

Rule: from the (single) red(2) cell to the (single) green(3) cell,
fill the shortest path with 8. Output keeps only 8s (everything else
becomes 0).

Combinatorial axes (8): grid_h, grid_w, palette_kind, wall_pct,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_path, no_seeds, multiple_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8584645d3102"
VERSION = "1.1.1"
TASK_ID = "8584645d3102"
SUMMARY = "Maze of gray walls + red and green seeds; output is shortest path painted 8."

INVARIANTS = [
    "outer border all gray(5)",
    "interior has scattered gray walls (<= 30% of cells)",
    "exactly one red(2) and one green(3) seed inside",
    "at least one bg-or-seed path connects the seeds (Manhattan distance >= 3)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_path", "no_seeds", "multiple_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "wall_pct":       {"type": "float", "default": "rng 0.10..0.25", "valid": "0..0.4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "compartmented",
                       "valid": "compartmented"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
    "density":        {"type": "str", "default": "medium", "valid": "medium"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: outer border is gray(5); exactly one red(2) and one green(3) inside."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # outer border must be gray(5)
    border_bad = []
    for c in range(w):
        if grid[0][c] != 5:
            border_bad.append(f"(0,{c})={grid[0][c]}")
        if grid[h - 1][c] != 5:
            border_bad.append(f"({h-1},{c})={grid[h-1][c]}")
    for r in range(1, h - 1):
        if grid[r][0] != 5:
            border_bad.append(f"({r},0)={grid[r][0]}")
        if grid[r][w - 1] != 5:
            border_bad.append(f"({r},{w-1})={grid[r][w-1]}")
    if border_bad:
        errs.append(f"border not all gray(5): {border_bad[:3]}")
    # check seed counts (skip for no_seeds degenerate)
    reds = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == 2]
    greens = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == 3]
    if not reds and not greens:
        return []  # no_seeds degenerate — allowed
    if len(reds) != 1:
        errs.append(f"expected exactly 1 red(2) cell; found {len(reds)}")
    if len(greens) != 1:
        errs.append(f"expected exactly 1 green(3) cell; found {len(greens)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)

    g = full_grid(h, w, 5)
    rng = ctx.draw_rng("layout")
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if rng.random() < 0.7:
                g[r][c] = 0

    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if g[r][c] == 0]
    if len(interior) < 4:
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                g[r][c] = 0
        interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]

    rng.shuffle(interior)
    rs, cs = interior[0]
    re_, ce = max(interior, key=lambda p: abs(p[0] - rs) + abs(p[1] - cs))

    g[rs][cs] = 2
    g[re_][ce] = 3

    def bfs_reachable(g, r, c):
        visited = {(r, c)}
        queue = [(r, c)]
        while queue:
            cr, cc = queue.pop(0)
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                nr, nc = cr+dr, cc+dc
                if not (0 <= nr < h and 0 <= nc < w): continue
                if g[nr][nc] == 5: continue
                if (nr, nc) in visited: continue
                visited.add((nr, nc))
                queue.append((nr, nc))
        return visited

    if (re_, ce) not in bfs_reachable(g, rs, cs):
        cr, cc = rs, cs
        while (cr, cc) != (re_, ce):
            if cr < re_: cr += 1
            elif cr > re_: cr -= 1
            elif cc < ce: cc += 1
            elif cc > ce: cc -= 1
            if g[cr][cc] == 5:
                g[cr][cc] = 0
        g[re_][ce] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 5)
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            g[r][c] = 0
    if name == "no_path":
        # walls completely separate red and green → BFS finds no path, rule output is empty
        for r in range(1, h - 1):
            g[r][4] = 5  # full wall splits the maze
        g[2][2] = 2
        g[5][6] = 3
        return g
    if name == "no_seeds":
        # no red or green cells → BFS has no source, rule has nothing to fill
        return g
    if name == "multiple_seeds":
        # multiple red and/or green cells → "exactly one of each" invariant violated, ambiguous source/sink
        g[2][2] = 2; g[2][5] = 2
        g[5][3] = 3; g[5][6] = 3
        return g
    return g
