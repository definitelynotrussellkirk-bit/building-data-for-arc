"""Generator for arc_puzzle_bank_eighteenth_21_bundle:easy_121_fill_horizontal_spans_between_matching_endpoints.

Rule: fill horizontal intervals between matching row endpoints.

Combinatorial axes (8): grid_h, grid_w, palette_kind, spans,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9fa30913fedc"
VERSION = "1.1.1"
TASK_ID = "9fa30913fedc"
SUMMARY = "Fill horizontal intervals between matching row endpoints."

INVARIANTS = [
    "background is 0",
    "active rows contain exactly two same-color endpoints",
    "endpoint pairs are separated by at least one zero",
    "output fills the inclusive row interval",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "spans":          {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_endpoint_pairs",
                       "valid": "row_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 active row with exactly two same-color endpoints separated by >=1 zero."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    active = 0
    for r in range(h):
        from collections import Counter
        row_freq = Counter(grid[r][c] for c in range(w) if grid[r][c] != 0)
        for color, cnt in row_freq.items():
            if cnt == 2:
                positions = [c for c in range(w) if grid[r][c] == color]
                c1, c2 = positions[0], positions[1]
                if c2 - c1 >= 2:  # at least one gap cell between
                    active += 1
                    break
    if active == 0:
        errs.append("no active row with two same-color endpoints separated by >=1 gap")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n = min(ctx.draw_int("spans", 3, 3), h, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n = min(ctx.draw_int("spans", 4, 5), h, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n = min(ctx.draw_int("spans", 3, 5), h, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), n)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for r, color in zip(rows, colors):
        c1 = rng.randint(0, w - 3)
        c2 = rng.randint(c1 + 2, w - 1)
        g[r][c1] = color
        g[r][c2] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only → no pair to fill span between
        g[1][2] = 4
        g[3][6] = 6
        return g
    if name == "mismatched_endpoints":
        # endpoints with different colors → "same-color pair" precondition fails
        g[1][1] = 4; g[1][6] = 6   # mismatched
        g[3][2] = 3; g[3][7] = 7   # mismatched
        return g
    if name == "span_already_filled":
        # span already non-zero → no empty cells to fill
        for c in range(1, 6): g[1][c] = 4   # full row
        g[3][1] = 6; g[3][3] = 9; g[3][5] = 6
        return g
    return g
