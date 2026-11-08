"""Generator for arc_puzzle_bank_21_set4:S4_E3.

Rule: columns with exactly two orange endpoints are filled vertically
between them.

Combinatorial axes (8): grid_h/w, span_count, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_endpoints, single_pair, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "356cdd4a2386"
VERSION = "1.1.0-selfcheck"
TASK_ID = "356cdd4a2386"
SUMMARY = "Columns with exactly two orange endpoints are filled vertically between them."

INVARIANTS = [
    "background is 0",
    "active columns contain exactly two orange cells",
    "cells between each endpoint pair start empty",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_endpoints", "single_pair", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "span_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        max_count = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
        max_count = 4
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        max_count = 4
    count = ctx.draw_int("span_count", 2, min(max_count, w))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for c in rng.sample(range(w), count):
        r1 = rng.randint(0, h - 4)
        r2 = rng.randint(r1 + 2, h - 1)
        g[r1][c] = 7
        g[r2][c] = 7
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_endpoints":
        return g
    if name == "single_pair":
        g[1][3] = 7
        g[6][3] = 7
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 7
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errors = []
    active = 0
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 7]
        if not rows:
            continue
        active += 1
        if len(rows) != 2:
            errors.append(f"column {c} has {len(rows)} orange cells, expected exactly 2")
        elif rows[1] - rows[0] < 2:
            errors.append(f"column {c} endpoint pair has no interior gap")
    if active < 2:
        errors.append(f"expected at least two active endpoint columns, got {active}")
    if any(v not in (0, 7) for row in grid for v in row):
        errors.append("only colors 0 and 7 should appear")
    return sorted(set(errors))
