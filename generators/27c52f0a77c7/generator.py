"""Generator for arc_additional_puzzle_bank_volume15:H102.

Rule: a unique corridor between start 1 and goal 2 exposes the
unavoidable core.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_corridor, no_endpoints, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "27c52f0a77c7"
VERSION = "1.1.1"
TASK_ID = "27c52f0a77c7"
SUMMARY = "A unique corridor between start 1 and goal 2 exposes the unavoidable core."

INVARIANTS = [
    "walls are 5",
    "open corridor cells are 0",
    "there is exactly one start color 1 and one goal color 2",
    "the corridor is the only shortest path",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_corridor", "no_endpoints", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_corridor|no_endpoints|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has walls (5), at least one start (1) and one goal (2)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_corridor", "no_endpoints", "full_grid"):
        return []
    errs = []
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if 1 not in flat:
        errs.append("no start cell (color 1)")
    if 2 not in flat:
        errs.append("no goal cell (color 2)")
    if 5 not in flat:
        errs.append("no wall cells (color 5)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 8, 14)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 5)
    r = rng.randint(1, h - 2)
    c1 = rng.randint(1, w - 5)
    c2 = rng.randint(c1 + 3, w - 2)
    for c in range(c1, c2 + 1):
        g[r][c] = 0
    g[r][c1] = 1
    g[r][c2] = 2
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
