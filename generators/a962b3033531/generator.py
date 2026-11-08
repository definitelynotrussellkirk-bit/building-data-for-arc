"""Generator for arc_puzzle_bank_nineteenth21:H130 — nearest-seed room fill.

Rule: wall color 5 partitions the grid into rooms.  Within each room, every
empty cell is recolored to the nearest non-wall seed color by Manhattan
distance; equal-distance disagreement becomes 9.

Combinatorial axes (8): grid_h, grid_w, n_seeds, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, single_seed, no_walls.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a962b3033531"
VERSION = "2.0.0"
TASK_ID = "a962b3033531"

SUMMARY = "Wall-bounded room with 2-5 colored seeds; zeros fill by nearest seed, ties become 9."

INVARIANTS = [
    "color 5 is the room wall",
    "background cells are 0",
    "default instances have 2-5 non-wall single-cell seeds inside a wall border",
    "at least one cell is equidistant from two differently colored seeds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "no_walls")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 5..11", "valid": "5..14"},
    "n_seeds":        {"type": "int", "default": "rng 2..5", "valid": "0..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "room_nearest_seed",
                       "valid": "room_nearest_seed"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_seeds|single_seed|no_walls"},
}


def _wall_box(h: int, w: int) -> list[list[int]]:
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5
        g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5
        g[h - 1][c] = 5
    return g


def _room_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    rooms = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 5 or (sr, sc) in seen:
                continue
            cells = []
            q = deque([(sr, sc)])
            seen.add((sr, sc))
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        q.append((nr, nc))
            rooms.append(cells)
    return rooms


def _has_forced_tie(grid) -> bool:
    seeds = [(r, c, v)
             for r, row in enumerate(grid)
             for c, v in enumerate(row)
             if v not in (0, 5)]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                continue
            ranked = sorted((abs(r - sr) + abs(c - sc), color) for sr, sc, color in seeds)
            if len(ranked) >= 2 and ranked[0][0] == ranked[1][0] and ranked[0][1] != ranked[1][1]:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Default invariant: a wall-bounded room with multiple colored seeds and a tie cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h < 5 or w < 5:
        errs.append("grid must be at least 5x5")
    palette = {v for row in grid for v in row}
    if not palette <= set(range(10)):
        errs.append("colors must be ARC digits 0..9")
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)):
        errs.append("left/right borders must be wall color 5")
    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errs.append("top/bottom borders must be wall color 5")
    seeds = [(r, c, v)
             for r, row in enumerate(grid)
             for c, v in enumerate(row)
             if v not in (0, 5)]
    if not (2 <= len(seeds) <= 5):
        errs.append(f"expected 2-5 interior seeds, got {len(seeds)}")
    if any(v == 9 for _, _, v in seeds):
        errs.append("input seeds should not use tie color 9")
    if not any(v == 0 for row in grid for v in row):
        errs.append("default room should contain empty cells for the rule to fill")
    for room in _room_components(grid):
        if not any(grid[r][c] not in (0, 5) for r, c in room):
            errs.append("every non-wall room should have at least one seed")
            break
    if not _has_forced_tie(grid):
        errs.append("expected at least one equidistant disagreement cell that will become 9")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 5, 7)
        n = ctx.draw_int("n_seeds", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_seeds", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 11)
        n = ctx.draw_int("n_seeds", 3, 4)

    rng = ctx.draw_rng("layout")
    g = _wall_box(h, w)
    colors = rng.sample([2, 3, 4, 6, 7, 8], n)

    # Force one pedagogically visible tie: two different seeds flank a zero cell.
    tie_r = rng.randint(1, h - 2)
    tie_c = rng.randint(2, w - 3)
    placements = [(tie_r, tie_c - 1, colors[0]), (tie_r, tie_c + 1, colors[1])]
    used = {(tie_r, tie_c - 1), (tie_r, tie_c + 1)}

    for color in colors[2:]:
        for _ in range(80):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            if (r, c) in used or (r == tie_r and c == tie_c):
                continue
            used.add((r, c))
            placements.append((r, c, color))
            break

    for r, c, color in placements:
        g[r][c] = color
    return g


def _draw_from_degenerate(name):
    g = _wall_box(5, 7)
    if name == "no_seeds":
        return g
    if name == "single_seed":
        g[2][3] = 4
        return g
    if name == "no_walls":
        g2 = full_grid(5, 7, 0)
        g2[2][2] = 2
        g2[2][4] = 3
        return g2
    return g
