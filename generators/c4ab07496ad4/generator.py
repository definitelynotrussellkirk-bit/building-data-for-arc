"""Generator for puzzle 009d5c81.

Rule: smaller shape kind → recolor for larger shape.
plus → red(2), bottom-full → green(3), else → orange(7).

Combinatorial axes (8): grid_h/w, shape_kind, palette_kind,
big_h, big_w, position_bias, anchor_corner, asymmetry_force.
Degenerates: equal_size, no_small, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid
from puzzle_generators.helpers.shape import PLUS_5

GENERATOR_ID = "c4ab07496ad4"
VERSION = "1.2.1"  # cap big shape vs grid so spread-bias floor-5 placement fits (easy w=9/10 gave randrange(5,4))
TASK_ID = "c4ab07496ad4"
SUMMARY = "Small + large shapes; rule recolors large by small's shape kind."

INVARIANTS = [
    "exactly 2 separated non-zero objects",
    "one is strictly smaller than the other",
    "shapes don't touch (>=1 bg between)",
    "shape_kind in {plus, bottom, other}",
]

SHAPE_KINDS = ("plus", "bottom", "other")
POSITION_BIASES = ("opposite_corners", "spread", "diagonal",
                   "row_aligned")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("equal_size", "no_small", "full_grid")
HELPFUL_TEXTURES = SHAPE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..18", "valid": "9..22"},
    "grid_w":         {"type": "int", "default": "rng 11..18", "valid": "9..22"},
    "shape_kind":     {"type": "str", "default": "rng helpful",
                       "valid": "plus|bottom|other"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "big_h":          {"type": "int", "default": "3", "valid": "3..5"},
    "big_w":          {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "opposite_corners|spread|diagonal|row_aligned"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for shape_kind",
                       "valid": "plus|bottom|other|equal_size|no_small|full_grid"},
}


SMALL_SHAPES = {
    "plus": PLUS_5,
    "bottom": [(0, 1), (1, 0), (1, 1), (1, 2)],
    "other": [(0, 0), (0, 1), (0, 2), (1, 1)],
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 9, 12
    elif difficulty == "hard":
        h_lo, h_hi = 16, 22
    else:
        h_lo, h_hi = 11, 18
    h = rng.randint(h_lo, h_hi)
    w = rng.randint(h_lo, h_hi)
    kind = (overrides.get("texture") or
            overrides.get("shape_kind")
            or ctx.draw_choice("shape_kind",
                               list(SHAPE_KINDS)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, 2, rng)
    small_color, big_color = palette[0], palette[1]
    big_h = int(overrides.get("big_h", 3))
    big_w = int(overrides.get("big_w",
                              ctx.draw_int("big_w", 4, 5)))
    big_h = max(3, min(5, big_h))
    big_w = max(3, min(6, big_w))
    # The "spread" bias places the big shape from a floor of 5 (to clear the
    # top-left small shape) up to h-big_h-1 / w-big_w-1. On the easy band's
    # small grids (h,w∈{9,10}) a width-5 big shape drops that hi below 5 →
    # empty randint(5, w-big_w-1)=randrange(5,4): the big shape is too wide to
    # be separated from the top-left small shape — genuine infeasibility, not
    # retry-exhaustion. Cap the big shape so the floor-5 placement always fits
    # (need hi≥lo ⇒ dim-big-1 ≥ 5 ⇒ big ≤ dim-6). Grids ≥11 keep big_h/big_w
    # unchanged, so default/hard and the other (fixed-position) biases are
    # byte-identical there.
    big_h = min(big_h, max(3, h - 6))
    big_w = min(big_w, max(3, w - 6))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         list(POSITION_BIASES)))
    g = full_grid(h, w, 0)
    sr, sc = _pick_small_pos(bias, h, w, rng)
    for dr, dc in SMALL_SHAPES[kind]:
        if 0 <= sr + dr < h and 0 <= sc + dc < w:
            g[sr + dr][sc + dc] = small_color
    br, bc = _pick_big_pos(bias, h, w, big_h, big_w, rng)
    draw_rect(g, br, bc, big_h, big_w, big_color)
    if rng.choice([True, False]) and bc + big_w - 1 < w:
        g[br][bc + big_w - 1] = 0
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 8]
    elif kind == "primary":
        pool = [1, 4]
    else:
        pool = [1, 4, 5, 6, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _pick_small_pos(bias, h, w, rng):
    if bias == "opposite_corners":
        return 1, 1
    if bias == "diagonal":
        return 1, 1
    if bias == "row_aligned":
        return h // 2, 1
    return rng.randint(1, 3), rng.randint(1, 3)


def _pick_big_pos(bias, h, w, big_h, big_w, rng):
    if bias == "opposite_corners":
        return h - big_h - 1, w - big_w - 1
    if bias == "diagonal":
        return h - big_h - 1, w - big_w - 1
    if bias == "row_aligned":
        return h // 2 - big_h // 2, w - big_w - 1
    return rng.randint(5, h - big_h - 1), rng.randint(5, w - big_w - 1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 distinct nonzero colors (small shape + large shape); >=1 nonzero cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) == 0:
        errors.append("no nonzero cells found")
    elif len(colors) < 2:
        errors.append(f"expected >=2 distinct nonzero colors (small+large shape), found {len(colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    h = w = 13
    g = full_grid(h, w, 0)
    if name == "equal_size":
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 3
                g[h - 4 + dr][w - 4 + dc] = 4
        return g
    if name == "no_small":
        draw_rect(g, h - 4, w - 5, 3, 4, 4)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3 if (r + c) % 2 == 0 else 4
        return g
    return g
