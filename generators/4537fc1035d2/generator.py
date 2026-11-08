"""Generator for arc_puzzle_bank_21_set4:S4_E5.

Green T-tetrominoes, in any rotation, are recolored magenta.

Combinatorial axes (8): grid_h, grid_w, palette_kind, t_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_t, all_t, no_green_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "4537fc1035d2"
VERSION = "1.1.1"
TASK_ID = "4537fc1035d2"

SUMMARY = "Green T-tetrominoes, in any rotation, are recolored magenta."

INVARIANTS = [
    "background is 0",
    "all input objects are green",
    "at least one object is a T tetromino up to rotation",
    "non-T green distractors remain green",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_t", "all_t", "no_green_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "6..15"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "6..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "t_count":        {"type": "int", "default": "rng 1..2", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "t_plus_distractors",
                       "valid": "t_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_T_SHAPES = [
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 0)],
]

_NON_T = [
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, all non-bg cells are green (color 3)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    non_bg = set(grid[r][c] for r in range(h) for c in range(w)) - {0}
    if not non_bg:
        errs.append("no non-bg cells (expected green T-tetrominoes)")
    if non_bg - {3}:
        errs.append(f"non-green non-bg colors found: {non_bg - {3}}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        t_count = ctx.draw_int("t_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        t_count = ctx.draw_int("t_count", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        t_count = ctx.draw_int("t_count", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shapes = [rng.choice(_T_SHAPES) for _ in range(t_count)]
    shapes.extend(rng.choice(_NON_T) for _ in range(rng.randint(1, 2)))
    rng.shuffle(shapes)
    for cells in shapes:
        if place_no_overlap(rng, g, cells, 3, padding=1, max_tries=400) is None:
            raise ValueError("could not place green object")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_t":
        # only non-T shapes → rule recolors nothing
        for r, c in [(1, 1), (1, 2), (1, 3), (1, 4)]: g[r][c] = 3  # I-tetromino
        for r, c in [(5, 5), (5, 6), (6, 5), (6, 6)]: g[r][c] = 3  # square
        return g
    if name == "all_t":
        # only T-shapes → rule recolors all (no contrast distractor)
        for r, c in [(1, 1), (1, 2), (1, 3), (2, 2)]: g[r][c] = 3
        for r, c in [(5, 5), (5, 6), (5, 7), (6, 6)]: g[r][c] = 3
        return g
    if name == "no_green_objects":
        # blank → no objects at all
        return g
    return g
