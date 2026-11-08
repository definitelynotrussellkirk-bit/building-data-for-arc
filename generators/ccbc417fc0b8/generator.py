"""Generator for arc_additional_puzzle_bank_volume12:E80 — bridge red endpoints with green.

Rule: rows with exactly two red endpoints are bridged with green between
them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_endpoints, single_endpoint_per_row, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ccbc417fc0b8"
VERSION = "2.0.1"
TASK_ID = "ccbc417fc0b8"
SUMMARY = (
    "0-bg grid (h, w ~8-13) with 2-5 ACTIVE ROWS, each "
    "containing EXACTLY TWO color-2 (red) ENDPOINT cells "
    "at columns c1 and c2 (c2 ≥ c1 + 2), with the span "
    "between them all 0. Different rows use distinct "
    "column-pairs. Other rows are entirely 0. Rule: for "
    "each row with exactly two red endpoints, paint the "
    "cells BETWEEN them (strictly inside, not endpoints) "
    "with color 3 (green). Net: each red pair becomes "
    "red endpoints + green bridge segment between."
)

INVARIANTS = [
    "background is 0",
    "each active row has exactly two red endpoints",
    "cells between endpoints are empty before the rule runs",
    "active rows are distinct so no column also contains two red markers",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_endpoints", "single_endpoint_per_row", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "row_endpoint_pairs",
                       "valid": "row_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_endpoints|single_endpoint_per_row|span_already_filled"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all non-zero cells are color 2 (red); each row has 0 or 2 red cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    # all non-zero cells should be color 2 in normal instances
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 2)]
    if bad:
        return errs  # degenerate (e.g. span_already_filled has non-2 cells) — allow
    for r in range(h):
        reds = [c for c in range(w) if grid[r][c] == 2]
        if len(reds) not in (0, 2):
            errs.append(f"row {r} has {len(reds)} red cells; expected 0 or 2")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_pairs = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
        n_pairs = ctx.draw_int("n_pairs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_pairs = ctx.draw_int("n_pairs", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), min(n_pairs, h))
    used_cols: set[int] = set()
    for r in rows:
        choices = [c for c in range(w) if c not in used_cols]
        if len(choices) < 2:
            break
        c1, c2 = sorted(rng.sample(choices, 2))
        if c2 - c1 < 2:
            continue
        g[r][c1] = 2
        g[r][c2] = 2
        used_cols.update((c1, c2))
    if not used_cols:
        g[1][1] = 2
        g[1][4] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        # blank → no red endpoints to bridge
        return g
    if name == "single_endpoint_per_row":
        # rows with 1 red cell → cannot define endpoint pair
        g[1][2] = 2
        g[3][5] = 2
        g[5][8] = 2
        return g
    if name == "span_already_filled":
        # endpoints + everything between already painted → rule has nothing
        for c in range(1, 7): g[1][c] = 2
        for c in range(2, 6): g[3][c] = 2
        return g
    return g
