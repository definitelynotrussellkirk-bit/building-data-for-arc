"""Generator for arc_additional_puzzle_bank_volume23:H161.

Rule: color-7 control count selects an exact graph-distance shell
around a seed.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_seed, no_walls, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7251d8fb61df"
VERSION = "2.0.1"  # dup-inputs/outputs 44%: seed (color 2) always at center, color-7 count (shell radius) only 2-4, grid 9-13 -> few distinct inputs. Vary seed position, color-7 count 1-6 (radius), and grid size -> many distinct distance-shell inputs/outputs.
TASK_ID = "7251d8fb61df"
SUMMARY = "Color-7 control count selects an exact graph-distance shell around a seed."

INVARIANTS = [
    "background is 0",
    "border walls are 5",
    "there is exactly one seed color 2",
    "color-7 control count is between 2 and 4",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seed", "no_walls", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "centered", "valid": "centered"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: border walls=5; exactly one color-2 seed; some color-7 markers; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    fives_border = any(grid[0][c] == 5 for c in range(w))
    if not fives_border:
        errs.append("expected border walls of color-5 at row 0")
    if len(twos) != 1:
        errs.append(f"expected exactly 1 color-2 seed, found {len(twos)}")
    if not sevens:
        errs.append("no color-7 control markers found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11); r_hi = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 13, 16); r_hi = 6
    else:
        h = ctx.draw_int("grid_h", 10, 15); w = ctx.draw_int("grid_w", 10, 15); r_hi = 5
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5
        g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5
        g[h - 1][c] = 5
    # color-7 markers: their COUNT sets the distance-shell radius
    n7 = rng.randint(1, min(r_hi, w - 3))
    for c in range(1, n7 + 1):
        g[1][c] = 7
    # seed (color 2) at a random interior cell below the marker row
    sr = rng.randint(2, h - 2); sc = rng.randint(1, w - 2)
    g[sr][sc] = 2
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_seed":
        for r in range(10):
            g[r][0] = 5
            g[r][9] = 5
        for c in range(10):
            g[0][c] = 5
            g[9][c] = 5
        return g
    if name == "no_walls":
        g[5][5] = 2
        g[1][1] = 7
        g[1][2] = 7
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 5
        return g
    return g
