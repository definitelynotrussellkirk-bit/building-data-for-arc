"""Generator for beb8660c.

Rule: bottom row of 8s + horizontal colored bars; sort by size desc,
pack to bottom-right above floor.

Combinatorial axes (8): grid_h/w, n_bars, palette_kind, size_skew,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_floor, no_bars, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a5557bf1391e"
VERSION = "2.1.0"
TASK_ID = "a5557bf1391e"
SUMMARY = (
    "0-bg grid (h~6-10, w~"
    "4-7) with: (a) ONE "
    "FULL-WIDTH FLOOR ROW "
    "of COLOR 8 at the "
    "BOTTOM (row h-1, all "
    "cols painted 8); (b) "
    "2-3 HORIZONTAL COLORED "
    "BARS above the floor — "
    "each bar is 1 ROW "
    "TALL, has a chosen "
    "LENGTH from 1..w-1 in "
    "a DISTINCT NON-8 color "
    "from a palette ({1, "
    "2, 3, 4, 6, 7, 9} or "
    "kind-restricted), "
    "placed at distinct "
    "rows in [0, h-2] with "
    "position bias "
    "(scattered/left-lean/"
    "right-lean/centered) "
    "and size skew (small/"
    "big/even). Bars don't "
    "overlap. Rule (SORT "
    "BARS BY SIZE DESC, "
    "PACK BOTTOM-RIGHT "
    "ABOVE FLOOR): "
    "identify all colored "
    "bars (each its own "
    "row segment) and "
    "their lengths. SORT "
    "by LENGTH "
    "DESCENDING (biggest "
    "first, tiebreak by "
    "color). Output is a "
    "fresh grid same h × w "
    "with the floor row "
    "preserved at the "
    "bottom (row h-1 = 8s)"
    ". Pack the sorted "
    "bars STACKED bottom-"
    "up, RIGHT-ALIGNED, "
    "each on its own row "
    "immediately above the "
    "floor (row h-2, h-3, "
    "h-4, ...). Net: bars "
    "sorted big-to-small, "
    "right-stacked on top "
    "of the 8-floor."
)

INVARIANTS = [
    "exactly one full-width row of 8s at the bottom",
    "2-3 horizontal bars at distinct rows above the floor",
    "each bar is 1 row tall, at least 1 cell wide, distinct color",
    "bars don't overlap",
]

POSITION_BIASES = ("scattered", "left_lean", "right_lean", "centered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_floor", "no_bars", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "n_bars":         {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "size_skew":      {"type": "str", "default": "rng",
                       "valid": "small|big|even"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 6, 3, 5
        nb_lo, nb_hi = 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 10, 14, 6, 10
        nb_lo, nb_hi = 3, 5
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 10, 4, 7
        nb_lo, nb_hi = 2, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    for c in range(w):
        g[h - 1][c] = 8
    n_bars = int(overrides.get("n_bars",
                               ctx.draw_int("n_bars", nb_lo, nb_hi)))
    n_bars = max(1, min(min(h - 2, w - 1, 5), n_bars))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, n_bars, rng)
    rows = rng.sample(range(0, h - 2), n_bars)
    sizes = rng.sample(range(1, w), min(n_bars, w - 1))
    skew = overrides.get("size_skew",
                         ctx.draw_choice("size_skew",
                                         ["small", "big", "even"]))
    if skew == "small":
        sizes = sorted(sizes)[:n_bars]
    elif skew == "big":
        sizes = sorted(sizes, reverse=True)[:n_bars]
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    for r, color, size in zip(rows, palette, sizes):
        if bias == "left_lean":
            c0 = 0
        elif bias == "right_lean":
            c0 = w - size
        elif bias == "centered":
            c0 = max(0, (w - size) // 2)
        else:
            c0 = rng.randint(0, w - size)
        for c in range(c0, c0 + size):
            g[r][c] = color
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 9]
    pool = [c for c in pool if c != 8]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 8, 6
    g = full_grid(h, w, 0)
    if name == "no_floor":
        g[3][2] = 2
        g[5][3] = 3
        return g
    if name == "no_bars":
        for c in range(w):
            g[h - 1][c] = 8
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 8
        return g
    return g


def _bars(grid):
    bars = []
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        c = 0
        while c < w:
            v = grid[r][c]
            if v in (0, 8):
                c += 1
                continue
            c0 = c
            while c < w and grid[r][c] == v:
                c += 1
            bars.append((r, c0, c - 1, v))
    return bars


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid has non-ARC color values")
    if any(grid[h - 1][c] != 8 for c in range(w)):
        errors.append("bottom row must be a full-width color-8 floor")
    if any(8 in row for row in grid[:-1]):
        errors.append("color 8 should appear only in the bottom floor row")
    bars = _bars(grid)
    if difficulty == "easy":
        lo, hi = 2, 2
    elif difficulty == "hard":
        lo, hi = 3, 5
    else:
        lo, hi = 2, 3
    if not (lo <= len(bars) <= hi):
        errors.append(f"expected {lo}..{hi} bars above floor, got {len(bars)}")
    rows = [b[0] for b in bars]
    colors = [b[3] for b in bars]
    if len(rows) != len(set(rows)):
        errors.append("bars must occupy distinct rows")
    if len(colors) != len(set(colors)):
        errors.append("bars must use distinct non-8 colors")
    return errors

