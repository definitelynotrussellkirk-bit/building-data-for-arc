"""Generator for arc_puzzle_bank_21_set24_bundle:hard_p02 — BFS path with portals.

Rule: find the shortest path from color-2 start to color-3 goal, avoiding
color-5 walls. Portal colors 6, 7, and 9 occur in pairs; stepping onto one
teleports to its mate. Empty cells on the traversed path are painted color 8.

Combinatorial axes (9): grid_h, grid_w, n_wall_cols, n_wall_rows,
n_portal_pairs, palette_kind, palette_size, position_bias, texture.
Degenerates: no_start, no_goal, walls_block_path.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d95333e055ae"
VERSION = "1.3.0"
TASK_ID = "d95333e055ae"

SUMMARY = "Start 2, goal 3, color-5 maze walls, optional paired portals 6/7/9; output path uses 8."

INVARIANTS = [
    "background is 0",
    "exactly one color-2 start cell and one color-3 goal cell",
    "walls are color 5, not output color 8",
    "portal colors 6, 7, and 9 occur either zero times or exactly twice",
    "input contains no color 8 because 8 is reserved for the output path",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_goal", "walls_block_path")
HELPFUL_TEXTURES = PALETTE_KINDS
PORTAL_COLORS = (6, 7, 9)

AXES = {
    "grid_h": {"type": "int", "default": "rng 9..12", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "rng 11..14", "valid": "11..16"},
    "n_wall_cols": {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "n_wall_rows": {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "n_portal_pairs": {"type": "int", "default": "rng 0..2", "valid": "0..3"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
    "palette_size": {"type": "int", "default": "rng 4..7", "valid": "3..7"},
    "position_bias": {"type": "str", "default": "maze_path_with_portals", "valid": "maze_path_with_portals"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "default|warm|cool|varied|no_start|no_goal|walls_block_path"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal instances use canonical colors: walls=5, portals=6/7/9, output path=8."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if (meta or {}).get("texture") in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    counts = Counter(v for row in grid for v in row)
    if counts[2] != 1:
        errs.append(f"expected exactly one color-2 start, found {counts[2]}")
    if counts[3] != 1:
        errs.append(f"expected exactly one color-3 goal, found {counts[3]}")
    if counts[8] != 0:
        errs.append("color 8 present in input; 8 is reserved for the solved path")
    bad = sorted(set(counts) - {0, 2, 3, 5, 6, 7, 9})
    if bad:
        errs.append(f"unexpected colors {bad}")
    for color in PORTAL_COLORS:
        if counts[color] not in (0, 2):
            errs.append(f"portal color {color} appears {counts[color]} times, expected 0 or 2")
    if counts[5] < max(1, min(h, w) // 2):
        errs.append("too few color-5 wall cells for a maze/pathfinding task")
    return errs


def _carve(g, cells):
    for r, c in cells:
        if g[r][c] == 5:
            g[r][c] = 0


def _l_path(h, w):
    cells = []
    for c in range(1, w - 1):
        cells.append((1, c))
    for r in range(2, h - 1):
        cells.append((r, w - 2))
    # Preserve order but remove the shared corner duplicate so portal pairs
    # cannot collapse to one coordinate.
    return list(dict.fromkeys(cells))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n_wall_cols = ctx.draw_int("n_wall_cols", 1, 1)
        n_wall_rows = ctx.draw_int("n_wall_rows", 0, 1)
        n_portal_pairs = ctx.draw_int("n_portal_pairs", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 16)
        n_wall_cols = ctx.draw_int("n_wall_cols", 2, 3)
        n_wall_rows = ctx.draw_int("n_wall_rows", 2, 3)
        n_portal_pairs = ctx.draw_int("n_portal_pairs", 1, 2)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
        n_wall_cols = ctx.draw_int("n_wall_cols", 1, 2)
        n_wall_rows = ctx.draw_int("n_wall_rows", 1, 2)
        n_portal_pairs = ctx.draw_int("n_portal_pairs", 0, 2)

    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    # Maze-like interior walls, then carve one guaranteed traversable L path.
    possible_cols = list(range(3, w - 3))
    rng.shuffle(possible_cols)
    for c in sorted(possible_cols[:n_wall_cols]):
        gap = rng.randint(1, h - 2)
        for r in range(1, h - 1):
            if r != gap:
                g[r][c] = 5

    possible_rows = list(range(3, h - 3))
    rng.shuffle(possible_rows)
    for r in sorted(possible_rows[:n_wall_rows]):
        gap = rng.randint(1, w - 2)
        for c in range(1, w - 1):
            if c != gap:
                g[r][c] = 5

    corridor = _l_path(h, w)
    _carve(g, corridor)
    sr, sc = corridor[0]
    gr, gc = corridor[-1]

    # Optional portals are placed on empty corridor cells so they are both live and reachable.
    candidates = [p for p in corridor[2:-2] if p not in ((sr, sc), (gr, gc))]
    rng.shuffle(candidates)
    for color in PORTAL_COLORS[:n_portal_pairs]:
        if len(candidates) < 2:
            break
        a = candidates.pop()
        b = candidates.pop()
        g[a[0]][a[1]] = color
        g[b[0]][b[1]] = color

    g[sr][sc] = 2
    g[gr][gc] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_start":
        g[6][10] = 3
        g[3][5] = 5; g[7][6] = 5
        return g
    if name == "no_goal":
        g[2][1] = 2
        g[3][5] = 5; g[7][6] = 5
        return g
    if name == "walls_block_path":
        g[2][1] = 2; g[6][10] = 3
        for r in range(h):
            g[r][6] = 5
        return g
    return g
