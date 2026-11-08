"""Generator for arc_puzzle_bank_21_set19_bundle:easy_p01.

Rule: rows contain two same-color endpoints with an empty span between
them; output draws the connecting line filling the span.

Combinatorial axes (8): grid_h, grid_w, palette_kind, span_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, span_already_filled, mismatched_endpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "539d4ac45311"
VERSION = "2.1.1"  # make the advertised 1..9 span_count override contract executable
TASK_ID = "539d4ac45311"
SUMMARY = (
    "0-bg grid (h~5-10, w~8-16) with 2-5 ENDPOINT PAIRS "
    "placed on distinct rows. Each pair places two "
    "SAME-COLOR cells on the SAME ROW at columns c1 < "
    "c2 with at least 1 empty cell between them. "
    "Different pairs use distinct non-bg colors. Rule: "
    "for every row that contains exactly two same-color "
    "cells at columns c1 < c2, FILL every cell at "
    "columns c1+1 .. c2-1 in that row with the "
    "pair's color (CONNECT the endpoints into a solid "
    "HORIZONTAL BAR). Endpoints stay; other rows "
    "untouched. Net: each pair of isolated row "
    "endpoints becomes a continuous colored horizontal "
    "line spanning the gap."
)

INVARIANTS = [
    "background is 0",
    "each active row has exactly two nonzero cells",
    "the two cells in an active row share one color and have only zeros between them",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "span_already_filled", "mismatched_endpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 8..16", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "span_count":     {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_endpoint_pairs",
                       "valid": "row_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|span_already_filled|mismatched_endpoints"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; active rows have exactly 2 non-bg cells of the same color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    active_rows = [r for r in range(h) if any(grid[r][c] != 0 for c in range(w))]
    if not active_rows:
        return errors  # degenerate (no_pairs) — allowed
    for r in active_rows:
        cells = [(c, grid[r][c]) for c in range(w) if grid[r][c] != 0]
        if len(cells) != 2:
            errors.append(f"row {r} has {len(cells)} non-bg cells, expected exactly 2")
            continue
        if cells[0][1] != cells[1][1]:
            errors.append(f"row {r} has two different colors ({cells[0][1]}, {cells[1][1]})")
        if cells[1][0] - cells[0][0] < 2:
            errors.append(f"row {r} endpoints are adjacent, so there is no empty span to fill")
    return errors


def _draw_span_count(ctx, overrides, *, default_lo: int, default_hi: int, h: int) -> int:
    """Preserve legacy random bands while honoring the advertised 1..9 override axis."""
    if overrides.get("span_count") is not None:
        return ctx.draw_int("span_count", 1, min(9, h))
    return ctx.draw_int("span_count", default_lo, min(default_hi, h))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 9)
        span_count = _draw_span_count(ctx, overrides, default_lo=2, default_hi=2, h=h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 12, 18)
        span_count = _draw_span_count(ctx, overrides, default_lo=4, default_hi=6, h=h)
    else:
        h = ctx.draw_int("grid_h", 5, 10)
        w = ctx.draw_int("grid_w", 8, 16)
        span_count = _draw_span_count(ctx, overrides, default_lo=2, default_hi=5, h=h)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)

    rows = rng.sample(range(h), span_count)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], span_count)
    for row, color in zip(rows, colors):
        gap = rng.randint(2, max(2, min(9, w - 2)))
        c1 = rng.randint(0, w - gap - 1)
        c2 = c1 + gap
        grid[row][c1] = color
        grid[row][c2] = color
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons in rows → no endpoints to bridge
        g[1][2] = 4
        g[3][5] = 6
        return g
    if name == "span_already_filled":
        # span between endpoints already has nonzero cells → rule's "empty span" precondition fails
        g[1][1] = 4; g[1][2] = 4; g[1][3] = 4; g[1][4] = 4   # no gap, all filled
        g[3][1] = 6; g[3][3] = 9; g[3][5] = 6                # midpoint has different color
        return g
    if name == "mismatched_endpoints":
        # endpoints with different colors → "same-color pair" rule precondition fails
        g[1][1] = 4; g[1][6] = 6   # mismatched
        g[3][2] = 3; g[3][7] = 7   # mismatched
        return g
    return g
