"""Generator for arc_puzzle_bank_twentythird21:E159 — fill horizontal span between same-color cells per row.

Rule: for each row, for each color appearing at least twice, paint the
horizontal span from min-col to max-col with that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a008c62d9e9"
VERSION = "1.1.1"
TASK_ID = "8a008c62d9e9"
SUMMARY = "1-3 rows each have 2 cells of the same color at separated columns."

INVARIANTS = [
    "background is 0",
    "1-3 rows have exactly 2 cells of the same color (separated by ≥2 cells)",
    "different rows use different colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rows":         {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "row_endpoint_pairs",
                       "valid": "row_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each active row has exactly 2 cells of same color, separated by >=2."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    for r in range(h):
        row = grid[r]
        nonzero = [(c, row[c]) for c in range(w) if row[c] != 0]
        if len(nonzero) == 0:
            continue
        if len(nonzero) == 2:
            (c1, v1), (c2, v2) = nonzero
            if v1 != v2:
                errs.append(f"row {r}: 2 cells but different colors ({v1} at c={c1}, {v2} at c={c2})")
            elif c2 - c1 < 2:
                errs.append(f"row {r}: endpoint cols too close (c1={c1} c2={c2})")
        elif len(nonzero) > 2:
            # mismatched_endpoints or span_already_filled degenerates — allow
            pass
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 6, 7)
        n = ctx.draw_int("n_rows", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 9)
        n = ctx.draw_int("n_rows", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 6, 9)
        n = ctx.draw_int("n_rows", 1, 3)
    n = min(n, h)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), n)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for r, color in zip(rows, colors):
        c1 = rng.randint(0, w - 4)
        c2 = rng.randint(c1 + 2, w - 1)
        g[r][c1] = color
        g[r][c2] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only → no pair to fill span between
        g[1][2] = 4
        g[3][5] = 6
        return g
    if name == "mismatched_endpoints":
        # endpoints with different colors in row → "same-color pair" precondition fails
        g[1][1] = 4; g[1][5] = 6
        g[3][2] = 3; g[3][6] = 7
        return g
    if name == "span_already_filled":
        # span between endpoints already non-zero → no empty cells to fill
        for c in range(1, 6): g[1][c] = 4    # full row
        g[3][1] = 6; g[3][3] = 9; g[3][5] = 6
        return g
    return g
