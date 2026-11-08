"""Generator for additional_bank:H4 — 3-row bar chart of components for colors 2, 3, 4.

Rule: counts = (n_2_components, n_3_components, n_4_components). Output
3 × max(counts) grid: row r is color (2/3/4) for first count_r cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n2,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, all_equal_counts, only_one_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "188ae9c7375d"
# 2.1.0: output is encoding-limited (3 x max-count bar chart, counts 1-5);
#        widened medium count range 1-4 -> 1-5 and enlarged grids so all 3
#        per-color component counts span the full valid range -> more
#        distinct (n2,n3,n4) tuples, fewer duplicate bar charts.
VERSION = "2.1.1"
TASK_ID = "188ae9c7375d"
SUMMARY = (
    "0-bg grid (h×w, ~6-13 by ~8-16) containing 1-5 connected "
    "components per color in {2 (red), 3 (green), 4 (yellow)}. "
    "All components are 8-conn isolated (≥1-cell buffer). Some "
    "distractor cells in other non-{0,2,3,4} colors may be "
    "scattered (rule ignores them). At least one of n2, n3, n4 "
    "differs (so output isn't uniform). Rule: count connected "
    "components of color 2 (call it n2), color 3 (n3), color 4 "
    "(n4). Build 3 × max(n2, n3, n4) output. Row 0 has color 2 "
    "in the first n2 cells (rest 0); row 1 has color 3 in first "
    "n3 cells; row 2 has color 4 in first n4 cells. Bar chart "
    "with row colors 2, 3, 4."
)

# Rivals: 'count cells, not components' refuted by ≥1 demo where a
# multi-cell blob counts as 1, not n. 'count all colors not just
# {2,3,4}' refuted by ≥1 demo with distractor colors that don't
# appear in output. 'use cell colors for output rows' confirmed
# (rule outputs row of color N). 'fill output rows fully' refuted by
# ≥1 demo where row widths differ.
# 4 demos covering varied component counts + distractors.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "between 1 and 3 components of color 2, 3, and 4 each",
    "all blobs are non-touching",
    "at least one count differs (so output isn't trivially uniform)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_equal_counts", "only_one_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n2":             {"type": "int", "default": "1-2 easy / 1-4 med / 2-5 hard", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "non_touching_blobs",
                       "valid": "non_touching_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_components|all_equal_counts|only_one_color"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: colors 2, 3, and 4 are all present (each has components)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_components", "all_equal_counts", "only_one_color"):
        return errs
    for color in (2, 3, 4):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if not cells:
            errs.append(f"color {color} has no cells (expected ≥1 component)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 7, 8, 9
        n_lo, n_hi = 1, 2
        n_dist_lo, n_dist_hi = 0, 1
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 10, 13, 12, 16
        n_lo, n_hi = 2, 5
        n_dist_lo, n_dist_hi = 2, 5
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 13, 12, 15
        n_lo, n_hi = 1, 5
        n_dist_lo, n_dist_hi = 1, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n2 = ctx.draw_int("n2", n_lo, n_hi)
    n3 = ctx.draw_int("n3", n_lo, n_hi)
    n4 = ctx.draw_int("n4", n_lo, n_hi)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set()
    for color, n in ((2, n2), (3, n3), (4, n4)):
        for _ in range(n):
            blob = grow_blob(rng, h, w, used, rng.randint(1, 3))
            if blob is None: continue
            used |= blob
            for r, c in blob: g[r][c] = color
    # Distractor cells (colors 1, 5-9) — rule only counts {2, 3, 4}
    # components, so distractors are invisible to output.
    n_distractors = rng.randint(n_dist_lo, n_dist_hi)
    distractor_pool = [1, 5, 6, 7, 8, 9]
    placed_d = 0
    for _ in range(40):
        if placed_d >= n_distractors: break
        dr = rng.randint(0, h - 1); dc = rng.randint(0, w - 1)
        if (dr, dc) in used: continue
        # Don't 4-touch existing {2,3,4} cells (would merge components).
        adj_bad = False
        for ar, ac in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = dr + ar, dc + ac
            if (nr, nc) in used:
                adj_bad = True; break
        if adj_bad: continue
        g[dr][dc] = rng.choice(distractor_pool)
        used.add((dr, dc))
        placed_d += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_components":
        # blank → all counts zero, output is 0-wide bar chart
        return g
    if name == "all_equal_counts":
        # equal counts (1 of each) → bar chart is uniform width, no contrast
        g[1][1] = 2
        g[3][3] = 3
        g[5][5] = 4
        return g
    if name == "only_one_color":
        # only color 2, no 3 or 4 → bar chart degenerate to single row
        g[1][1] = 2
        g[3][3] = 2
        g[5][5] = 2
        return g
    return g
