"""Generator for arc_puzzle_bank_eighteenth_21_bundle:easy_124_right_pack_each_row_preserving_order.

Combinatorial axes (8): grid_h, grid_w, palette_kind, active_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: already_right_packed, no_active_rows, fully_packed_rows.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c64bcbdda754"
VERSION = "1.1.0"
TASK_ID = "c64bcbdda754"
SUMMARY = "Right-pack each row's nonzero values while preserving order."

INVARIANTS = [
    "background is 0",
    "rows transform independently",
    "nonzero values keep left-to-right order",
    "packed values sit against the right edge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("already_right_packed", "no_active_rows", "fully_packed_rows")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "active_rows":    {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "with_left_gaps",
                       "valid": "with_left_gaps"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|already_right_packed|no_active_rows|fully_packed_rows"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 8, 9)
        active = min(ctx.draw_int("active_rows", 3, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 10, 11)
        active = min(ctx.draw_int("active_rows", 4, 5), h)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 8, 11)
        active = min(ctx.draw_int("active_rows", 3, 5), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), active)
    forced = rng.choice(rows)
    for r in rows:
        k = rng.randint(1, min(5, w))
        cols = sorted(rng.sample(range(w), k))
        if r == forced and cols == list(range(w - k, w)):
            cols = sorted(rng.sample(range(0, w - 1), k))
        for c, color in zip(cols, rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k)):
            g[r][c] = color
    return g


def _right_packed(row):
    vals = [v for v in row if v != 0]
    return row == [0] * (len(row) - len(vals)) + vals


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    active = [row for row in grid if any(v != 0 for v in row)]
    if not active:
        errors.append("expected at least one active row")
    if active and all(_right_packed(row) for row in active):
        errors.append("at least one row must have left gaps to close")
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 5, 10
    g = full_grid(h, w, 0)
    if name == "already_right_packed":
        # rows already right-packed → rule is identity, no visible movement
        for r, vs in [(1, [3, 4, 5]), (2, [6, 7]), (4, [8, 9, 2])]:
            for i, v in enumerate(vs):
                g[r][w - len(vs) + i] = v
        return g
    if name == "no_active_rows":
        # empty grid → nothing to right-pack
        return g
    if name == "fully_packed_rows":
        # rows are entirely nonzero → no gaps to close, identity output
        for r in range(h):
            for c in range(w):
                g[r][c] = 1 + ((r + c) % 7)
        return g
    return g
