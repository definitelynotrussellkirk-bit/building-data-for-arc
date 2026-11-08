"""Generator for arc_puzzle_bank_fourteenth_21_bundle:easy_92_fill_horizontal_intervals.

Rule: place same-color endpoint pairs in separate rows; output fills
each row's interval inclusively.

Combinatorial axes (8): grid_h, grid_w, palette_kind, segments,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f2480e18069"
VERSION = "2.1.0"  # add executable self_check coverage for horizontal endpoint pairs
TASK_ID = "4f2480e18069"
SUMMARY = (
    "0-bg grid (h~7-10, w~8-12) "
    "with 2-4 SAME-COLOR "
    "HORIZONTAL ENDPOINT PAIRS, "
    "each on a DIFFERENT ROW, at "
    "columns (c1, c2) with c2 ≥ "
    "c1 + 2 (≥1 bg cell between "
    "them). Each pair uses a "
    "DISTINCT non-zero color from "
    "{1..9}. Active rows have "
    "exactly 2 cells in their "
    "color; the interval between "
    "is initially 0. Rule (FILL "
    "ROW INTERVAL BETWEEN "
    "ENDPOINTS): for EACH ROW "
    "with exactly 2 SAME-COLOR "
    "ENDPOINTS, FILL the INCLUSIVE "
    "INTERVAL between them (every "
    "cell from min_c to max_c in "
    "that row) with the pair's "
    "COLOR. Rows without "
    "endpoints stay 0. Net: each "
    "horizontal endpoint pair "
    "becomes a solid filled "
    "interval."
)

INVARIANTS = [
    "background is 0",
    "each active row contains one same-color endpoint pair",
    "the endpoints in each row have at least one blank cell between them",
    "active endpoint colors are distinct across the grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "segments":       {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_endpoint_pairs",
                       "valid": "row_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|mismatched_endpoints|span_already_filled"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        target = min(ctx.draw_int("segments", 2, 2), h, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        target = min(ctx.draw_int("segments", 3, 4), h, 9)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        target = min(ctx.draw_int("segments", 2, 4), h, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), target)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], target)
    for r, color in zip(rows, colors):
        c1 = rng.randint(0, w - 3)
        c2 = rng.randint(c1 + 2, w - 1)
        g[r][c1] = color
        g[r][c2] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only → no pair
        g[1][2] = 4
        g[3][6] = 6
        return g
    if name == "mismatched_endpoints":
        # mismatched row endpoints → "same-color pair" precondition fails
        g[1][1] = 4; g[1][6] = 6
        g[3][2] = 3; g[3][7] = 7
        return g
    if name == "span_already_filled":
        # span between endpoints already non-zero
        for c in range(1, 6): g[1][c] = 4
        g[3][1] = 6; g[3][3] = 9; g[3][5] = 6
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    rows = []
    colors_seen: set[int] = set()
    for r, row in enumerate(grid):
        vals = [(c, v) for c, v in enumerate(row) if v != 0]
        if not vals:
            continue
        rows.append(r)
        row_colors = {v for _, v in vals}
        if len(row_colors) != 1 or len(vals) != 2:
            errs.append(f"row {r} should contain exactly one same-color endpoint pair")
            continue
        color = vals[0][1]
        if color in colors_seen:
            errs.append("endpoint colors should be distinct across active rows")
        colors_seen.add(color)
        c1, c2 = vals[0][0], vals[1][0]
        if c2 - c1 < 2:
            errs.append(f"row {r} pair needs a visible blank gap")
        if any(row[c] != 0 for c in range(c1 + 1, c2)):
            errs.append(f"row {r} interval should be empty before fill")
    min_expected = 3 if difficulty == "hard" else 2
    if len(rows) < min_expected:
        errs.append(f"expected at least {min_expected} active endpoint rows, got {len(rows)}")
    return errs
