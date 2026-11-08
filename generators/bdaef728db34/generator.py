"""Generator for arc_puzzle_bank_21_set13_bundle:easy_m01.

Horizontal same-color runs are present; the solver keeps only the leftmost
cell of each run.

Combinatorial axes (8): grid_h, grid_w, palette_kind, run_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_singletons, runs_touching, no_runs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bdaef728db34"
    # 2.2.0: fail closed if all requested runs cannot be placed; add self_check.
    # 2.1.0: allow runs to ABUT a different-color run (no zero gap) sometimes,
# which exercises the rule's "left neighbor has a different color ->
# leftmost" branch. Same-color adjacency is still forbidden (would merge
# into one run). Also widened size/run-count ranges.
VERSION = "2.2.0"
TASK_ID = "bdaef728db34"
SUMMARY = (
    "0-bg grid (h×w, ~6-9 by ~8-12) with 3-5 horizontal RUNS of "
    "non-zero cells. Each run: a contiguous horizontal segment "
    "of length 2-5 in a single non-zero color. Runs are placed "
    "in different rows or with ≥1 zero gap between same-row "
    "runs. Different runs use distinct colors (or repeat). "
    "Rule: for each cell, output the cell's color if it's the "
    "LEFTMOST of its same-color horizontal run (i.e., either "
    "col=0 or the cell to its left has a different color), else "
    "0. Output: only the leftmost cell of each horizontal run "
    "survives."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-5 horizontal same-color runs of length 2+",
    "runs are separated by ≥1 zero (within same row)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_singletons", "runs_touching", "no_runs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "run_count":      {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "scattered_rows",
                       "valid": "scattered_rows"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        run_count = ctx.draw_int("run_count", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        run_count = ctx.draw_int("run_count", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 12)
        run_count = ctx.draw_int("run_count", 3, 5)
    colors = ctx.draw_distinct_colors("colors", n=min(run_count, 6), exclude={0})
    rng = ctx.draw_rng("layout")

    for _board in range(40):
        g = full_grid(h, w, 0)
        placed = 0
        for _ in range(600):
            if placed >= run_count:
                return g
            length = rng.randint(2, min(5, w))
            r = rng.randrange(h)
            c1 = rng.randint(0, w - length)
            c2 = c1 + length - 1
            color = colors[placed % len(colors)]
            # The run's own cells must be empty.
            if any(g[r][c] != 0 for c in range(c1, c2 + 1)):
                continue
            # Same-color neighbours on either side would merge the runs, so they
            # are forbidden. A DIFFERENT non-zero colour may abut (allowed ~40%);
            # otherwise require a zero gap.
            left = g[r][c1 - 1] if c1 - 1 >= 0 else 0
            right = g[r][c2 + 1] if c2 + 1 < w else 0
            if left == color or right == color:
                continue
            allow_abut = rng.random() < 0.4
            if not allow_abut and (left != 0 or right != 0):
                continue
            for c in range(c1, c2 + 1):
                g[r][c] = color
            placed += 1
    raise ValueError("could not place requested horizontal runs")


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "all_singletons":
        # nonzero cells are singletons (length 1) → "leftmost of run" = the cell itself, rule is identity
        for r, c, v in [(1, 2, 4), (3, 5, 5), (5, 7, 6)]:
            g[r][c] = v
        return g
    if name == "runs_touching":
        # adjacent runs of different colors with no zero gap → ambiguous run boundaries
        for c, v in [(1, 3), (2, 3), (3, 4), (4, 4), (5, 5)]:
            g[2][c] = v
        return g
    if name == "no_runs":
        # empty grid → no runs to extract leftmost from
        return g
    return g


def _runs(grid):
    out = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            color = row[c]
            c1 = c
            while c < len(row) and row[c] == color:
                c += 1
            out.append((r, c1, c - 1, color))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    runs = _runs(grid)
    long_runs = [run for run in runs if run[2] - run[1] + 1 >= 2]
    expected = (3, 3) if difficulty == "easy" else ((4, 5) if difficulty == "hard" else (3, 5))
    if not (expected[0] <= len(long_runs) <= expected[1]):
        errs.append(f"expected {expected[0]}-{expected[1]} horizontal runs length>=2, found {len(long_runs)}")
    if len(long_runs) != len(runs):
        errs.append("normal examples should not contain singleton distractor runs")
    for r, c1, c2, color in long_runs:
        if c1 > 0 and grid[r][c1 - 1] == color:
            errs.append("same-color run merged with left neighbour")
        if c2 + 1 < len(grid[0]) and grid[r][c2 + 1] == color:
            errs.append("same-color run merged with right neighbour")
    return errs
