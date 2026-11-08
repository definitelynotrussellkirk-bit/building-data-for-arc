"""Generator for arc_puzzle_bank_21_set8_s:S8_E3.

Rule: cells on the left of a full color-8 vertical bar are mirrored
to the right side.

Combinatorial axes (8): grid_h, grid_w, palette_kind, source_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, source_on_right, already_mirrored.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1d032e35937"
VERSION = "1.2.1"  # add executable self_check for bar/mirror invariants.
TASK_ID = "e1d032e35937"
SUMMARY = "Cells on the left of a full color-8 vertical bar are mirrored to the right."

INVARIANTS = [
    "background is 0",
    "there is exactly one full-height color-8 divider",
    "all source cells are left of the divider",
    "mirrored destinations on the right are blank and in bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "source_on_right", "already_mirrored")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..15"},
    "grid_w":         {"type": "int", "default": "rng odd 9..13", "valid": "7..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "source_count":   {"type": "int", "default": "rng 3..6", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 2..6", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "left_of_divider",
                       "valid": "left_of_divider"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..6", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_divider|source_on_right|already_mirrored"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 9)
        count = ctx.draw_int("source_count", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        count = ctx.draw_int("source_count", 6, 10)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 15)
        count = ctx.draw_int("source_count", 3, 7)
    if w % 2 == 0:
        w += 1
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    b = w // 2
    for r in range(h):
        g[r][b] = 8
    palette = [2, 3, 4, 6, 7, 9]
    for idx, (r, c) in enumerate(rng.sample([(r, c) for r in range(h) for c in range(b)], count)):
        g[r][c] = palette[idx % len(palette)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    b = w // 2
    if name == "no_divider":
        # no full-height 8-col → mirror axis undefined
        g[1][1] = 3; g[3][2] = 7; g[5][3] = 4
        return g
    for r in range(h):
        g[r][b] = 8
    if name == "source_on_right":
        # all sources placed right of divider → no left-side cells to mirror
        g[1][b + 2] = 3; g[3][b + 3] = 7; g[5][b + 1] = 4
        return g
    if name == "already_mirrored":
        # left and right are already mirror-symmetric → rule no-op
        for r, c in [(1, 1), (1, w - 2), (3, 2), (3, w - 3)]:
            g[r][c] = 3
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariant for the mirror-left-across-color-8-bar task."""
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a nonempty list-of-lists"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    bad = sorted({v for row in grid for v in row if not isinstance(v, int) or v < 0 or v > 9})
    if bad:
        errs.append(f"invalid ARC colors: {bad}")

    full_bar_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(full_bar_cols) != 1:
        errs.append(f"expected exactly one full-height color-8 divider, found {len(full_bar_cols)}")
        return errs
    b = full_bar_cols[0]
    sources = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if c == b:
                continue
            if v == 8:
                errs.append(f"color 8 appears off divider at {(r, c)}")
            if v == 0:
                continue
            if c > b:
                errs.append(f"source cell appears right of divider at {(r, c)}")
            else:
                sources.append((r, c, v))
                mc = 2 * b - c
                if not (0 <= mc < w):
                    errs.append(f"mirror destination out of bounds for {(r, c)} -> {(r, mc)}")
                elif grid[r][mc] != 0:
                    errs.append(f"mirror destination {(r, mc)} is not blank")
    if len(sources) < 2:
        errs.append(f"expected at least two source cells left of divider, found {len(sources)}")
    return errs
