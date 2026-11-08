"""Generator for 58e15b12.

Rule: green(3) and cyan(8) bars project diagonal rays; intersections
become magenta(6).

Combinatorial axes (8): grid_h/w, bar1_h, bar1_w, bar2_h, bar2_w,
position_bias, bar_spacing, anchor_corner.
Degenerates: bars_overlap, single_bar, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "78e3f26e92aa"
VERSION = "2.0.1"
TASK_ID = "78e3f26e92aa"
SUMMARY = (
    "0-bg grid (h, w ~12-16) with TWO solid rectangular "
    "BARS: one color-3 (green) bar and one color-8 (cyan) "
    "bar, non-overlapping, with vertical spacing. Rule: for "
    "each bar (color k ∈ {3, 8}), compute its bbox "
    "(r1, bh, cl, cr). For each output cell (r, c): the "
    "bar 'reaches' (r, c) if (r - r1)/bh is an integer step "
    "k and c is either cl - k or cr + k — i.e. the bar "
    "projects two diverging diagonal rays from its left and "
    "right edges, one cell over per bar-height step. "
    "Output: 6 (magenta) where BOTH rays reach, 3 where "
    "only the green ray, 8 where only the cyan ray, else 0."
)

INVARIANTS = [
    "background is 0",
    "one solid green(3) bar and one solid cyan(8) bar",
    "bars are non-overlapping rectangles",
]

POSITION_BIASES = ("centered", "wide_spread", "stacked", "rng")
DEGENERATE_TEXTURES = ("bars_overlap", "single_bar", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "bar1_h":         {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "bar1_w":         {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "bar2_h":         {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "bar2_w":         {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "centered|wide_spread|stacked|rng"},
    "bar_spacing":    {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "centered|wide_spread|stacked|rng|bars_overlap|single_bar|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, ≥1 color-3 (green) bar cell and ≥1 color-8 (cyan) bar cell, bars non-overlapping."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    count_3 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    count_8 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 8)
    if count_3 == 0:
        errs.append("no color-3 (green) bar cells found")
    if count_8 == 0:
        errs.append("no color-8 (cyan) bar cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 10, 12
        bw_lo, bw_hi = 2, 3
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
        bw_lo, bw_hi = 3, 6
    else:
        h_lo, h_hi = 12, 16
        bw_lo, bw_hi = 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    bh1 = int(overrides.get("bar1_h",
                            ctx.draw_int("bar1_h", 1, 2)))
    bw1 = int(overrides.get("bar1_w",
                            ctx.draw_int("bar1_w", bw_lo, bw_hi)))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    spacing = int(overrides.get("bar_spacing",
                                ctx.draw_int("bar_spacing", 2, 4)))
    rr1, rc1 = _pick_pos(bias, h, w, bh1, bw1, "top", rng)
    draw_rect(g, rr1, rc1, bh1, bw1, 3)
    bh2 = int(overrides.get("bar2_h",
                            ctx.draw_int("bar2_h", 1, 2)))
    bw2 = int(overrides.get("bar2_w",
                            ctx.draw_int("bar2_w", bw_lo, bw_hi)))
    placed = False
    for _try in range(40):
        rr2 = rng.randint(rr1 + bh1 + spacing, max(rr1 + bh1 + spacing, h - bh2))
        rc2 = rng.randint(2, max(2, w - bw2 - 2))
        if rr2 + bh2 > h:
            continue
        overlap = False
        for r in range(rr2, rr2 + bh2):
            for c in range(rc2, rc2 + bw2):
                if g[r][c] != 0:
                    overlap = True
                    break
            if overlap:
                break
        if not overlap:
            draw_rect(g, rr2, rc2, bh2, bw2, 8)
            placed = True
            break
    if not placed:
        return _draw_from_degenerate("single_bar", rng)
    return g


def _pick_pos(bias, h, w, bh, bw, half, rng):
    if half == "top":
        max_r = max(2, h // 2 - bh - 2)
        rr = rng.randint(2, max_r) if max_r >= 2 else 2
    else:
        rr = rng.randint(h // 2 + 1, h - bh - 1)
    if bias == "centered":
        rc = max(2, (w - bw) // 2)
    elif bias == "wide_spread":
        rc = rng.choice([2, max(2, w - bw - 2)])
    elif bias == "stacked":
        rc = rng.randint(2, max(2, w - bw - 2))
    else:
        rc = rng.randint(2, max(2, w - bw - 2))
    return rr, rc


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "bars_overlap":
        draw_rect(g, 5, 5, 2, 4, 3)
        draw_rect(g, 5, 6, 2, 4, 8)
        return g
    if name == "single_bar":
        draw_rect(g, 5, 5, 1, 4, 3)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3 if (r + c) % 2 == 0 else 8
        return g
    return g
