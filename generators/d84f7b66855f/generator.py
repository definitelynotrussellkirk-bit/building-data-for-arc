"""Generator for ARC task 833966f4.

Rule: row reorder. Output rows = [1, 0, 2, 4, 3, 5, ...] of input.
Effectively swap rows 0↔1 and 3↔4.

Combinatorial axes: grid_w, palette_size, row_pattern. Degenerates:
identical_rows, monochrome, only_swap_pairs_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d84f7b66855f"
VERSION = "1.1.0"
TASK_ID = "d84f7b66855f"
SUMMARY = "A 5+ row grid; rule swaps rows 0/1 and 3/4."

INVARIANTS = [
    "input has ≥5 rows",
    "row pairs (0,1) and (3,4) differ so the swaps are visible",
    "colors are sampled from a small palette",
]

ROW_PATTERNS = ("random", "structured", "banded", "palette_per_row")
DEGENERATE_TEXTURES = ("identical_rows", "monochrome", "only_swap_pairs_match")
HELPFUL_TEXTURES = ROW_PATTERNS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5..10"},
    "grid_w":         {"type": "int", "default": "rng 1..12", "valid": "1..15"},
    "palette_size":   {"type": "int", "default": "rng 3..7", "valid": "1..10"},
    "row_pattern":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ROW_PATTERNS)},
    "texture":        {"type": "str", "default": "alias for row_pattern",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        w_lo, w_hi, c_lo, c_hi = 1, 5, 2, 3
    elif difficulty == "hard":
        w_lo, w_hi, c_lo, c_hi = 9, 12, 5, 8
    else:
        w_lo, w_hi, c_lo, c_hi = 1, 12, 3, 7
    h = int(overrides.get("grid_h", 5))
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_colors = int(overrides.get("palette_size",
                                 ctx.draw_int("palette_size", c_lo, c_hi)))
    palette = list(ctx.draw_distinct_colors("palette", n=max(2, n_colors)))
    pattern = (overrides.get("texture")
               or overrides.get("row_pattern")
               or ctx.draw_choice("row_pattern", list(ROW_PATTERNS)))
    g = _make_grid(pattern, h, w, palette, rng)
    if g[0] == g[1]:
        g[1][0] = palette[1] if g[1][0] != palette[1] else palette[2 % len(palette)]
    if g[3] == g[4]:
        g[4][0] = palette[2 % len(palette)] if g[4][0] != palette[2 % len(palette)] else palette[1]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """≥5 rows; rows 0/1 and 3/4 must differ so swaps are visible."""
    errs = []
    h = len(grid)
    if h < 5:
        errs.append(f"need ≥5 rows, got {h}")
        return errs
    if grid[0] == grid[1]:
        errs.append("row 0 equals row 1, swap is invisible")
    if grid[3] == grid[4]:
        errs.append("row 3 equals row 4, swap is invisible")
    return errs


def _make_grid(pattern, h, w, palette, rng):
    g = full_grid(h, w, palette[0])
    if pattern == "random":
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice(palette)
    elif pattern == "structured":
        for r in range(h):
            color = palette[r % len(palette)]
            for c in range(w):
                g[r][c] = color if rng.random() < 0.7 else rng.choice(palette)
    elif pattern == "banded":
        for r in range(h):
            for c in range(w):
                g[r][c] = palette[(c + r) % len(palette)]
    elif pattern == "palette_per_row":
        for r in range(h):
            color = palette[r % len(palette)]
            for c in range(w):
                g[r][c] = color
    return g


def _draw_from_degenerate(name, h, w, rng):
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if name == "identical_rows":
        g = full_grid(h, w, palette[0])
        for r in range(h):
            for c in range(w):
                g[r][c] = palette[(c) % 3]
        return g
    if name == "monochrome":
        c0 = palette[0]
        return [[c0] * w for _ in range(h)]
    if name == "only_swap_pairs_match":
        g = full_grid(h, w, palette[0])
        same_pair_a = [palette[1] if rng.random() < 0.5 else palette[2] for _ in range(w)]
        g[0] = list(same_pair_a)
        g[1] = list(same_pair_a)
        same_pair_b = [palette[3] if rng.random() < 0.5 else palette[4] for _ in range(w)]
        g[3] = list(same_pair_b)
        g[4] = list(same_pair_b)
        for r in (2,) + tuple(range(5, h)):
            for c in range(w):
                g[r][c] = palette[(r + c) % len(palette)]
        return g
    return [[palette[0]] * w for _ in range(h)]
