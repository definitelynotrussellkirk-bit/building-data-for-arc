"""Generator for 2204b7a8.

Rule: full rows and full cols (uniform color, not 3 or 0) are
indicators. Each 3-cell takes nearest indicator's color.

Combinatorial axes (8): grid_h/w, n_rows, n_cols, n_threes, palette_kind,
position_bias, anchor_corner, asymmetry_force.
Degenerates: no_indicators, no_threes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a069ad7f8880"
VERSION = "1.1.1"
TASK_ID = "a069ad7f8880"
SUMMARY = "Sparse 0-bg with 1-2 full rows + 1-2 full cols of distinct colors and 3-5 scattered 3-cells."

INVARIANTS = [
    ">=1 full row and/or >=1 full col of single non-{0,3} color",
    "3-5 scattered 3-cells in the interior",
    "indicator rows/cols use distinct colors",
]

POSITION_BIASES = ("scattered", "centered", "corners", "row_aligned")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_indicators", "no_threes", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..14"},
    "n_rows":         {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_cols":         {"type": "int", "default": "rng 0..2", "valid": "0..3"},
    "n_threes":       {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 full row or col of single non-{0,3} color (indicator); >=1 color-3 cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Check for >=1 full row of single non-{0,3} color
    indicator_found = False
    for r in range(h):
        row_vals = set(grid[r])
        if len(row_vals) == 1 and row_vals != {0} and row_vals != {3}:
            indicator_found = True
            break
    if not indicator_found:
        for c in range(w):
            col_vals = set(grid[r][c] for r in range(h))
            if len(col_vals) == 1 and col_vals != {0} and col_vals != {3}:
                indicator_found = True
                break
    if not indicator_found:
        errs.append("no full row or column of a single non-{0,3} indicator color")
    # Check for >=1 color-3 cell
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not threes:
        errs.append("no color-3 cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 6, 8
        nt_lo, nt_hi = 1, 3
    elif difficulty == "hard":
        h_lo, h_hi = 12, 14
        nt_lo, nt_hi = 4, 8
    else:
        h_lo, h_hi = 8, 12
        nt_lo, nt_hi = 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, 3, rng)
    n_rows = int(overrides.get("n_rows",
                               ctx.draw_int("n_rows", 1, 2)))
    n_rows = max(1, min(3, n_rows))
    n_cols = int(overrides.get("n_cols",
                               ctx.draw_int("n_cols", 0, 2 if n_rows == 1 else 1)))
    n_cols = max(0, min(3, n_cols))
    rows = rng.sample(range(h), min(n_rows, h))
    cols = rng.sample(range(w), min(n_cols, w))
    pi = 0
    for r in rows:
        for c in range(w):
            g[r][c] = palette[pi % len(palette)]
        pi += 1
    for c in cols:
        for r in range(h):
            g[r][c] = palette[pi % len(palette)]
        pi += 1
    n_threes = int(overrides.get("n_threes",
                                 ctx.draw_int("n_threes", nt_lo, nt_hi)))
    n_threes = max(1, min(10, n_threes))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    placed = 0
    for _try in range(120):
        if placed >= n_threes:
            break
        if bias == "centered":
            r = rng.randint(max(0, h // 4), min(h - 1, 3 * h // 4))
            c = rng.randint(max(0, w // 4), min(w - 1, 3 * w // 4))
        elif bias == "corners":
            r = rng.choice([rng.randint(0, 1), rng.randint(h - 2, h - 1)])
            c = rng.choice([rng.randint(0, 1), rng.randint(w - 2, w - 1)])
        elif bias == "row_aligned":
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
        else:
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = 3
            placed += 1
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 4]
    else:
        pool = [1, 2, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 3)]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_indicators":
        for _ in range(4):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = 3
        return g
    if name == "no_threes":
        for c in range(w):
            g[3][c] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g
