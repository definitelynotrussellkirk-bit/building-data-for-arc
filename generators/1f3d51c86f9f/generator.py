"""Generator for arc_additional_puzzles_21_set9:H62 — connect color-pair endpoints with L-path.

Rule: for each non-9 color (except 0) that has exactly 2 cells, draw
an L-shaped path between them. Try horizontal-then-vertical first; if
that path crosses another color (not 0 and not same color), fall back
to vertical-then-horizontal. Color 9 acts as a wall/obstacle.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance, color_counts, has_row_gap, interior_cells, is_full_frame_component, norm

GENERATOR_ID = "1f3d51c86f9f"
VERSION = "2.0.0"
TASK_ID = "1f3d51c86f9f"

SUMMARY = (
    "0-bg grid with: (a) several color-9 walls (often a vertical line "
    "or scattered); (b) several pairs of cells in distinct non-9 "
    "colors (each color appears at EXACTLY 2 cells). Rule: for each "
    "non-9 color with exactly 2 cells, draw an L-shaped path between "
    "them: try horizontal-then-vertical via the bend at (r1, c2); if "
    "any interior cell of that path is non-zero and non-same-color, "
    "fall back to vertical-then-horizontal via (r2, c1). Paint the "
    "path with the color, preserving the endpoints. Color-9 walls and "
    "0-cells along the path are overwritten."
)

# Rivals: 'output is input' refuted by demos with ≥1 2-cell pair.
# 'draw straight line' refuted by demos with L-shape visible.
# 'use color 9 for paths' refuted by demos preserving original colors.
# 'don't connect if walls block' refuted by demos showing L-path
# routes around. 'connect every cell (not just pairs)' refuted by
# demos where pair-cells get connected, not all cells. 3 demos with
# multiple 2-cell pairs at varied positions pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 color-9 wall cell (the rule's barrier)",
    "≥1 non-9 color appears EXACTLY 2 times in the input",
    "the 2 cells per color are at distinct rows AND distinct cols (so L-path is non-trivial)",
    "no other color appears more than 2 times (so the rule's '2-cell' filter is unambiguous)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); pair count comes from the unkeyed layout rng and scales with
# difficulty, so it isn't an override axis.
AXES = {
    "grid_h": {"type": "int", "default": "rng 8..11", "valid": "7..14",
               "doc": "Grid height (easy 7..9, medium 8..11, hard 11..14)."},
    "grid_w": {"type": "int", "default": "rng 8..11", "valid": "7..14",
               "doc": "Grid width (easy 7..9, medium 8..11, hard 11..14)."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_pairs_lo, n_pairs_hi = 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_pairs_lo, n_pairs_hi = 3, 4
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n_pairs_lo, n_pairs_hi = 2, 3
    g = full_grid(h, w, 0)
    # Place a wall column or scattered 9s
    if rng.random() < 0.5:
        # Full vertical wall
        wc = rng.randint(w // 3, 2 * w // 3)
        for r in range(h):
            g[r][wc] = 9
    else:
        # Scattered 9s
        n_walls = rng.randint(2, 5)
        for _ in range(n_walls * 4):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = 9
    n_pairs = rng.randint(n_pairs_lo, n_pairs_hi)
    pair_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], n_pairs)
    for color in pair_colors:
        for _ in range(40):
            r1 = rng.randint(0, h - 1); c1 = rng.randint(0, w - 1)
            r2 = rng.randint(0, h - 1); c2 = rng.randint(0, w - 1)
            if r1 == r2 or c1 == c2:
                continue
            if g[r1][c1] != 0 or g[r2][c2] != 0:
                continue
            g[r1][c1] = color
            g[r2][c2] = color
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    counts = color_counts(grid)
    if counts.get(9, 0) < 1:
        errs.append("expected at least one color-9 wall/obstacle")
    pair_colors = [c for c, n in counts.items() if c not in (0, 9) and n == 2]
    if not pair_colors:
        errs.append("expected at least one non-9 color with exactly two endpoints")
    for color, n in counts.items():
        if color not in (0, 9) and n > 2:
            errs.append(f"color {color} appears more than twice")
    for color in pair_colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]:
            errs.append(f"color {color} pair should require a nontrivial L path")
    return errs
