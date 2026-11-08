"""Generator for arc_puzzle_bank_21_set4:S4_E1 — recolor 2x2 blue squares to red.

Rule: exact blue 2x2 square objects are recolored red; other blue
shapes remain.

Combinatorial axes (8): grid_h, grid_w, palette_kind, square_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_squares, all_squares, no_blue_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "51db77fe24c5"
VERSION = "1.2.0"
TASK_ID = "51db77fe24c5"

SUMMARY = "Exact blue 2x2 square objects are recolored red; other blue shapes remain."

INVARIANTS = [
    "background is 0",
    "all input objects are blue",
    "at least one object is exactly a 2x2 square",
    "other blue objects are not exact 2x2 squares",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_squares", "all_squares", "no_blue_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "square_count":   {"type": "int", "default": "rng 1..2", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "blue_squares_with_distractors",
                       "valid": "blue_squares_with_distractors"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SQUARE = [(0, 0), (0, 1), (1, 0), (1, 1)]
_NON_SQUARES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    [(0, 0), (1, 0), (1, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        square_count = ctx.draw_int("square_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        square_count = ctx.draw_int("square_count", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        square_count = ctx.draw_int("square_count", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shapes = [_SQUARE for _ in range(square_count)]
    shapes.extend(rng.choice(_NON_SQUARES) for _ in range(rng.randint(1, 2)))
    rng.shuffle(shapes)
    for cells in shapes:
        if place_no_overlap(rng, g, cells, 1, padding=1, max_tries=400) is None:
            raise ValueError("could not place blue object")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_squares":
        # only non-2x2 blue objects → rule recolors nothing
        for r, c in [(1, 1), (2, 1), (3, 1)]: g[r][c] = 1   # vertical tromino
        for r, c in [(5, 4), (5, 5), (5, 6)]: g[r][c] = 1   # horizontal tromino
        return g
    if name == "all_squares":
        # only 2x2 squares → all recolored, no contrast distractor
        for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]: g[r][c] = 1
        for r, c in [(5, 5), (5, 6), (6, 5), (6, 6)]: g[r][c] = 1
        return g
    if name == "no_blue_objects":
        # blank → no objects at all
        return g
    return g

def _blue_components(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    square = nonsquare = 0
    for cells in _blue_components(grid):
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        norm = sorted((r - min(rs), c - min(cs)) for r, c in cells)
        if norm == [(0, 0), (0, 1), (1, 0), (1, 1)]:
            square += 1
        else:
            nonsquare += 1
    msgs = []
    if square < 1:
        msgs.append("no exact blue 2x2 square target")
    if nonsquare < 1:
        msgs.append("no non-square blue distractor")
    return msgs
