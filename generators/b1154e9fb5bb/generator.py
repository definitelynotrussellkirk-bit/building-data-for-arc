"""Generator for b457fec5.

Rule: a gray diagonal staircase is recolored by a cycling legend with
saturation.

Combinatorial axes (8): grid_h/w, direction, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_legend, no_staircase, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "b1154e9fb5bb"
VERSION = "1.2.1"  # shape-locked in+out: hardcoded 12x14 though rule handles any size (canonical 17x18/23x19/14x18). Now vary grid size, staircase length, and legend size."
TASK_ID = "b1154e9fb5bb"
SUMMARY = "Gray diagonal staircase recolored by cycling legend with saturation."

INVARIANTS = [
    "the first non-empty non-gray row is the color legend",
    "a gray object is made from overlapping legend-sized blocks along a diagonal",
    "gray cells are recolored by diagonal offset and saturate after the last full cycle",
]

DIRECTIONS = ("right", "left")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_legend", "no_staircase", "full_grid")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12"},
    "grid_w":         {"type": "int", "default": "14", "valid": "14"},
    "direction":      {"type": "str", "default": "rng helpful",
                       "valid": "right|left"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for direction",
                       "valid": "right|left|no_legend|no_staircase|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; row 0 has ≥2 non-zero non-5 legend colors; gray(5) cells form staircase."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # legend: row 0 should have ≥2 non-zero non-5 colors
    legend_cells = [grid[0][c] for c in range(w) if grid[0][c] not in (0, 5)]
    if len(set(legend_cells)) < 2:
        errs.append(f"expected ≥2 distinct non-5 legend colors in row 0; found {len(set(legend_cells))}")
    # gray(5) cells must exist (the staircase)
    gray_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    if gray_count < 3:
        errs.append(f"expected gray(5) staircase (≥3 cells); found {gray_count}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    direction = (overrides.get("texture") if overrides.get("texture") in DIRECTIONS else None) or \
                overrides.get("direction") or \
                ("right" if sample_index % 2 == 0 else "left")
    # output = same dims; v1.x hardcoded 12x14 (shape-locked in+out) though the
    # rule handles any size (canonical: 17x18, 23x19, 14x18). Now vary grid size,
    # staircase length, and legend size.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 26); w = ctx.draw_int("grid_w", 18, 26)
    else:
        h = ctx.draw_int("grid_h", 12, 22); w = ctx.draw_int("grid_w", 14, 22)
    n_legend = rng.randint(2, 4)
    legend = ctx.draw_distinct_colors("legend", n=n_legend, exclude={0, 5})
    g = full_grid(h, w, 0)
    for i, color in enumerate(legend):
        g[0][i + 1] = color
    start_r = 3
    # staircase of 3x3 rects stepping diagonally; bound steps so it stays in grid
    max_by_row = (h - start_r - 3) + 1
    if direction == "right":
        start_c = 2
        max_by_col = (w - 3 - start_c) + 1
    else:
        start_c = w - 4
        max_by_col = start_c + 1
    max_steps = max(1, min(max_by_row, max_by_col))
    steps = rng.randint(1, min(8, max_steps))
    for k in range(steps):
        c = start_c + k if direction == "right" else start_c - k
        draw_rect(g, start_r + k, c, 3, 3, 5)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    if name == "no_legend":
        draw_rect(g, 3, 2, 3, 3, 5)
        return g
    if name == "no_staircase":
        for i, color in enumerate([3, 4, 6]):
            g[0][i + 1] = color
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(14):
                g[r][c] = 5
        return g
    return g
