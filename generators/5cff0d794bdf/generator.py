"""Generator for arc_puzzle_bank_twentyfirst_21_bundle:easy_141_fill_between_matching_column_markers.

Rule: columns with two matching endpoint markers are filled between
them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_endpoints, endpoints_adjacent, single_endpoint_per_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5cff0d794bdf"
VERSION = "2.0.1"
TASK_ID = "5cff0d794bdf"
SUMMARY = (
    "0-bg grid (h~9-14, w~7-10) with 3-5 ENDPOINT "
    "PAIRS placed in distinct columns. Each pair "
    "places two SAME-COLOR cells in the same column at "
    "rows r1 < r2 with r2 ≥ r1 + 2 (so there is at "
    "least one empty cell between them). Different "
    "pairs use distinct non-bg colors. Rule: for each "
    "column containing exactly two same-color cells "
    "at rows r1 and r2, FILL every cell at rows r1+1 "
    ".. r2-1 in that column with that color "
    "(BRIDGING the gap into a solid vertical bar). "
    "Endpoints stay; non-pair columns stay 0. Net: "
    "each pair of isolated endpoints becomes a "
    "continuous colored vertical line."
)

INVARIANTS = [
    "background is 0",
    "each active column has exactly two nonzero markers",
    "the two column markers have the same color",
    "marker interiors are blank",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_endpoints", "endpoints_adjacent", "single_endpoint_per_col")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "4..24"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "3..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cols":           {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "column_pairs",
                       "valid": "column_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 7, 8)
        target = min(ctx.draw_int("cols", 3, 3), w)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 9, 10)
        target = min(ctx.draw_int("cols", 4, 5), w)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 7, 10)
        target = min(ctx.draw_int("cols", 3, 5), w)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), target)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], target)
    for c, color in zip(cols, colors):
        r0 = rng.randint(0, h - 3)
        r1 = rng.randint(r0 + 2, h - 1)
        g[r0][c] = color
        g[r1][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 8
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        # empty grid → no endpoint pairs to fill between
        return g
    if name == "endpoints_adjacent":
        # markers immediately adjacent → no gap between them, fill is empty
        g[2][2] = 4; g[3][2] = 4
        g[5][5] = 6; g[6][5] = 6
        return g
    if name == "single_endpoint_per_col":
        # one marker per column → no second endpoint to span to
        g[3][2] = 4
        g[5][5] = 6
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    pair_colors = []
    for c in range(w):
        nz = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if not nz:
            continue
        if len(nz) != 2:
            errs.append(f"column {c} has {len(nz)} nonzero cells, expected two endpoints")
            continue
        (r0, v0), (r1, v1) = nz
        if v0 != v1:
            errs.append(f"column {c} endpoint colors differ")
        if r1 <= r0 + 1:
            errs.append(f"column {c} endpoints are adjacent/no gap")
        pair_colors.append(v0)
    min_cols = 4 if difficulty == "hard" else 3
    if len(pair_colors) < min_cols:
        errs.append(f"expected at least {min_cols} active columns, got {len(pair_colors)}")
    if len(pair_colors) != len(set(pair_colors)):
        errs.append("endpoint-pair colors should be distinct across columns")
    return errs
