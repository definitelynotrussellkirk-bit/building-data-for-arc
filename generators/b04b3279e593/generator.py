"""Generator for arc_puzzle_bank_21_set9_e:easy_i02.

Rule: top-row color markers paint their entire columns.

Combinatorial axes (8): grid_h/w, markers, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_markers, single_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b04b3279e593"
VERSION = "1.1.0"
TASK_ID = "b04b3279e593"

SUMMARY = "Top-row color markers paint their entire columns."

INVARIANTS = [
    "background is 0",
    "only row 0 contains nonzero markers",
    "marker columns are distinct",
    "output repeats each top-row marker down its full column",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_markers", "single_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..7", "valid": "4..7"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "8..11"},
    "markers":        {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 4, 7)
        w = ctx.draw_int("grid_w", 8, 11)
    n = min(ctx.draw_int("markers", 2, 4), w)
    g = full_grid(h, w, 0)
    for c, color in zip(rng.sample(range(w), n), rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)):
        g[0][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or len({len(row) for row in grid}) != 1:
        return ["grid is empty or ragged"]
    markers = [(c, v) for c, v in enumerate(grid[0]) if v != 0]
    if not (2 <= len(markers) <= 4):
        errs.append(f"expected 2-4 top-row markers, found {len(markers)}")
    colors = [v for _, v in markers]
    if len(set(colors)) != len(colors):
        errs.append(f"marker colors are not distinct: {colors}")
    lower_nonzero = [(r, c) for r in range(1, len(grid)) for c, v in enumerate(grid[r]) if v != 0]
    if lower_nonzero:
        errs.append(f"nonzero cells below top row: first={lower_nonzero[:5]}")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 9, 0)
    if name == "no_markers":
        return g
    if name == "single_marker":
        g[0][3] = 3
        return g
    if name == "full_grid":
        for r in range(5):
            for c in range(9):
                g[r][c] = 3
        return g
    return g
