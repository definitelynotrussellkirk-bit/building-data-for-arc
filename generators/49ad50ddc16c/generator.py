"""Generator for arc_puzzle_bank_21_set14_bundle:medium_n07 — per-col gravity-down within wall segments.

Rule: walls are color 5. Within each column, between consecutive
walls (or wall and grid edge), gravity-down: collect non-zero,
non-5 values and place them at the BOTTOM of the segment, preserving
their order.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49ad50ddc16c"
VERSION = "2.1.0"  # reduce over-scattered cells to canonical-like object counts
TASK_ID = "49ad50ddc16c"

SUMMARY = (
    "Grid with color-5 walls scattered as singletons or short segments. "
    "Within each column, segments between consecutive walls (or wall "
    "and grid edge) hold scattered non-zero non-5 colored cells. Rule: "
    "for each column, scan top-down. Walls (5) preserved in place. "
    "Within each segment between walls, collect all non-zero non-5 "
    "values in top-to-bottom order and pack them at the BOTTOM of "
    "the segment, with 0 padding above. Equivalent to per-column "
    "gravity-down within wall-bounded segments."
)

# Rivals: 'output is input' refuted by demos with non-bottom values.
# 'gravity-up' refuted by demos showing bottom alignment.
# 'sort values within segment' refuted by demos preserving top-to-
# bottom order. 'gravity across walls' refuted by demos where walls
# stop the drop. 'gravity-left (horizontal)' refuted by demos showing
# vertical drop. 'remove walls' refuted by demos preserving 5s.
# 4 demos with mixed segments and ≥2 wall positions pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "≥1 color-5 wall cell (the rule's segment boundary)",
    "scattered non-zero non-5 values in segments — any colors",
    "≥2 segments per column on average so the per-column gravity is observable",
    "≥1 segment has a non-trivially-packable column (≥1 zero between non-zero values)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_values", "single_segment")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "6..16"},
    "wall_density":   {"type": "float", "default": "rng 0.05..0.15", "valid": "0..0.3"},
    "value_density":  {"type": "float", "default": "rng 0.15..0.3", "valid": "0..0.5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        wall_lo, wall_hi = 2, 3
        value_lo, value_hi = 4, 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 8, 11)
        wall_lo, wall_hi = 4, 5
        value_lo, value_hi = 7, 9
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        wall_lo, wall_hi = 3, 5
        value_lo, value_hi = 5, 8
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 6)
    n_walls = ctx.draw_int("n_walls", wall_lo, wall_hi)
    n_values = ctx.draw_int("n_values", value_lo, value_hi)

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        cells = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(cells)
        for r, c in cells[:n_walls]:
            g[r][c] = 5
        free = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        rng.shuffle(free)
        for r, c in free[:n_values]:
            g[r][c] = rng.choice(palette)
        # Reroll already-packed examples; every normal demo should show at
        # least one falling value, but not by flooding the grid with values.
        if _gravity_down(g) != g:
            return g
    raise ValueError("could not realize nontrivial column-gravity layout")


def _gravity_down(g):
    h, w = len(g), len(g[0])
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if g[r][c] == 5:
                out[r][c] = 5
    for c in range(w):
        start = 0
        while start < h:
            end = start
            while end < h and g[end][c] != 5:
                end += 1
            vals = [g[r][c] for r in range(start, end) if g[r][c] not in (0, 5)]
            for i, v in enumerate(reversed(vals)):
                out[end - 1 - i][c] = v
            start = end + 1
    return out


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # Values but no walls — gravity-down for whole column
        g[1][3] = 4; g[3][3] = 7
        g[2][7] = 8; g[6][7] = 6
        return g
    if name == "no_values":
        # Walls but no values — output equals input
        for r in range(0, h, 2):
            g[r][5] = 5
        return g
    if name == "single_segment":
        # One wall but values only on one side
        for c in range(w):
            g[4][c] = 5
        g[1][2] = 4; g[2][3] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    if not any(v == 5 for row in grid for v in row):
        errors.append("expected at least one color-5 wall")
    if not any(v not in (0, 5) for row in grid for v in row):
        errors.append("expected at least one movable non-zero, non-wall value")

    n_values = sum(1 for row in grid for v in row if v not in (0, 5))
    n_walls = sum(1 for row in grid for v in row if v == 5)
    if n_values > 10:
        errors.append(f"too many movable values for canonical-like sparse task: {n_values}")
    if n_walls > 6:
        errors.append(f"too many wall cells for canonical-like sparse task: {n_walls}")
    if _gravity_down(grid) == grid:
        errors.append("all movable values are already gravity-packed; rule branch is hidden")
    return errors
