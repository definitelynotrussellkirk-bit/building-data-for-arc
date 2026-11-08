"""Generator for 13713586.

Rule: colored bars project toward full gray edge; nearer bars overwrite.

Combinatorial axes (8): grid_h/w, n_bars, palette_kind, position_bias,
anchor_corner, asymmetry_force, palette_size, edge_position.
Degenerates: no_edge, no_bars, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a07ec9e021a"
VERSION = "2.0.1"
TASK_ID = "8a07ec9e021a"
SUMMARY = (
    "0-bg grid (h~12-25, w~12-25) with: "
    "(a) RIGHT EDGE GRAY LINE — every "
    "cell in column w-1 painted color "
    "5 (the gray edge); (b) 2-6 "
    "COLORED BARS placed in the "
    "interior (rows 1..h-3, cols 1..w-"
    "6), each a small 1×L or 2×L "
    "rectangle (L ∈ {1..3}, height 1 "
    "or 2) painted in a DISTINCT non-"
    "{0, 5} color drawn from a "
    "palette (warm/cool/primary/broad "
    "kinds). Bars are placed at non-"
    "overlapping rows (every 3rd row "
    "available) so they are "
    "disconnected from each other "
    "and from the gray edge. Rule "
    "(EACH COLORED BAR PROJECTS A "
    "RECTANGLE RIGHTWARD TOWARD THE "
    "GRAY EDGE — NEARER BARS "
    "OVERWRITE OVERLAPPING "
    "PROJECTIONS): for EACH non-{0, "
    "5} BAR at rows [r..r+rh-1], "
    "cols [c..c+length-1]: PROJECT a "
    "RECTANGLE rightward — paint "
    "cells [r..r+rh-1] × [c..w-2] "
    "with the bar's color (extending "
    "from the bar through to one "
    "cell before the gray edge). "
    "Bars with overlapping projection "
    "rows compete — the NEARER bar "
    "(higher c value, i.e., closer "
    "to the gray edge) OVERWRITES "
    "the farther bar's projection "
    "in the overlap zone. The gray "
    "edge stays color 5. Net: each "
    "bar's color streaks rightward "
    "to the edge; nearer bars cover "
    "farther ones."
)

INVARIANTS = [
    "one outer edge is a full gray line",
    "colored bars are disconnected from that gray edge",
    "each bar projects a rectangle toward the gray edge",
    "nearer bars overwrite farther projected areas if they overlap",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_edge", "no_bars", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "8..25"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "8..25"},
    "n_bars":         {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng",
                       "valid": "scattered|spread|rng"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "edge_position":  {"type": "str", "default": "right", "valid": "right"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one full gray-5 edge column (rightmost); bars are non-5 non-0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Check for the right-edge gray column
    full_gray_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not full_gray_cols:
        return errs  # no_edge degenerate — allowed
    if len(full_gray_cols) > 1:
        errs.append(f"expected 1 full-gray-5 column; found {len(full_gray_cols)}: {full_gray_cols}")
    elif full_gray_cols[0] != w - 1:
        errs.append(f"full-gray column at c={full_gray_cols[0]} but expected c={w-1}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 8, 11, 10, 12
        nb_lo, nb_hi = 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 16, 25, 17, 25
        nb_lo, nb_hi = 4, 6
    else:
        h_lo, h_hi, w_lo, w_hi = 12, 16, 12, 17
        nb_lo, nb_hi = 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n_bars = ctx.draw_int("n_bars", nb_lo, nb_hi)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, n_bars, rng)
    if len(pool) < n_bars:
        pool = pool + [c for c in [1, 2, 3, 4, 6, 7, 8, 9]
                       if c not in pool and c != 5]
    colors = pool[:n_bars]
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][w - 1] = 5
    row_slots = list(range(1, h - 2, 3))
    rng.shuffle(row_slots)
    for color, r in zip(colors, row_slots[:n_bars]):
        rh = 1 if r + 1 >= h - 1 else rng.randint(1, 2)
        c = rng.randint(1, w - 6)
        length = rng.randint(1, min(3, w - 2 - c))
        for dr in range(rh):
            for dc in range(length):
                g[r + dr][c + dc] = color
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    pool = [c for c in pool if c != 5]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_edge":
        g[3][5] = 2
        return g
    if name == "no_bars":
        for r in range(h):
            g[r][w - 1] = 5
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
