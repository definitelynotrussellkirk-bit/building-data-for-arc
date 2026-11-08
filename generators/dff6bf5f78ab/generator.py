"""Generator for arc_additional_puzzles_21_set4:E23 — Connect 2-cell pairs of color 1 within each row.

Rule: each row with exactly 2 cells of color 1 → fill all cells between
them (inclusive) with 1.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_paired_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_singletons, three_in_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dff6bf5f78ab"
VERSION = "2.1.0"  # palette-locked(2c) is rule-intrinsic (rule only fills color-1 rows). Widen grids (up to 14x14) and ACTUALLY use n_paired_rows by difficulty (was hardcoded 2-3) -> more bars per grid.
TASK_ID = "dff6bf5f78ab"
SUMMARY = (
    "0-bg grid (h~5-7, w~"
    "8-10) with 2-3 "
    "ACTIVE ROWS each "
    "containing EXACTLY 2 "
    "COLOR-1 (blue) cells "
    "at distinct columns "
    "separated by ≥2 col "
    "gap, PLUS 1 "
    "DISTRACTOR ROW with "
    "ONE ISOLATED color-1 "
    "cell. Other rows are "
    "0. Rule (FOR EACH "
    "ROW WITH EXACTLY 2 "
    "COLOR-1 CELLS, FILL "
    "ALL CELLS BETWEEN "
    "THEM INCLUSIVE WITH "
    "COLOR 1): For EACH "
    "ROW r: COUNT non-bg "
    "color-1 cells. If "
    "EXACTLY 2 at "
    "columns (c1, c2): "
    "PAINT every cell in "
    "row r from "
    "min(c1, c2) to "
    "max(c1, c2) "
    "(inclusive) with "
    "COLOR 1. Rows with "
    "0, 1, or ≥3 color-"
    "1 cells stay "
    "unchanged. Net: 2-"
    "cell rows fill in "
    "to solid blue bars; "
    "1-cell distractors "
    "remain as singletons."
)

INVARIANTS = [
    "≥2 rows have exactly 2 cells of color 1, separated by ≥1 0-cell",
    "≥1 distractor row has only 1 cell of color 1 (won't trigger)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_singletons", "three_in_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_paired_rows":  {"type": "int", "default": "rng 2..3", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "row_pairs_with_distractor",
                       "valid": "row_pairs_with_distractor"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
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
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 9)
        n_pairs = ctx.draw_int("n_paired_rows", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_pairs = ctx.draw_int("n_paired_rows", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n_pairs = ctx.draw_int("n_paired_rows", 3, 5)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used_rows = set()
    # cap paired rows so there is always a free row left for the distractor
    n_pairs = min(n_pairs, h - 1)
    for _ in range(n_pairs):
        for _ in range(20):
            r = rng.randint(0, h - 1)
            if r in used_rows:
                continue
            cs = sorted(rng.sample(range(w), 2))
            if cs[1] - cs[0] >= 2:
                g[r][cs[0]] = 1; g[r][cs[1]] = 1
                used_rows.add(r)
                break
    free_rows = [r for r in range(h) if r not in used_rows]
    if free_rows:
        r = rng.choice(free_rows)
        g[r][rng.randint(0, w - 1)] = 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    colors = {v for row in grid for v in row}
    if not colors <= {0, 1}:
        errs.append(f"input should contain only 0/1, got {sorted(colors)}")
    row_counts = [sum(1 for v in row if v == 1) for row in grid]
    pair_rows = [i for i, n in enumerate(row_counts) if n == 2]
    singleton_rows = [i for i, n in enumerate(row_counts) if n == 1]
    if len(pair_rows) < 2:
        errs.append(f"expected at least two trigger rows, got {len(pair_rows)} counts={row_counts}")
    if not singleton_rows:
        errs.append(f"expected a one-cell distractor row, counts={row_counts}")
    for r in pair_rows:
        cols = [c for c, v in enumerate(grid[r]) if v == 1]
        if cols[1] - cols[0] < 2:
            errs.append(f"trigger row {r} lacks a zero gap between endpoints: {cols}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no rows with pairs, rule has no effect
        return g
    if name == "single_singletons":
        # every row has only 1 cell → predicate "exactly 2" never true, rule is identity
        g[1][3] = 1
        g[3][5] = 1
        g[5][2] = 1
        return g
    if name == "three_in_row":
        # rows with 3 1-cells → predicate "exactly 2" fails, rule has no effect
        g[1][1] = 1; g[1][3] = 1; g[1][7] = 1
        g[3][2] = 1; g[3][5] = 1; g[3][8] = 1
        return g
    return g
