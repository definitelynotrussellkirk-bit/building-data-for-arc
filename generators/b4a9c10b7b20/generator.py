"""Generator for arc_puzzle_bank_21_set11_s:S11_M4 — Draw rect borders for color pairs.

Rule: for each color with exactly 2 cells (any position), paint the
rectangle border between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_pair_aligned, pair_too_close.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "b4a9c10b7b20"
VERSION = "1.1.1"
TASK_ID = "b4a9c10b7b20"
SUMMARY = "2-3 colors each with exactly 2 cells at distinct rows/cols."

INVARIANTS = [
    "between 2 and 3 distinct colors",
    "each color has exactly 2 cells",
    "each color pair spans a non-degenerate rectangle",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_pair_aligned", "pair_too_close")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "diagonal_pairs",
                       "valid": "diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|single_pair_aligned|pair_too_close"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-bg colors; each color appears exactly 2 times;
    each pair of cells is at different rows AND different columns (non-degenerate rect)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    from collections import Counter
    color_cells: dict[int, list[tuple[int, int]]] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                color_cells.setdefault(v, []).append((r, c))
    if len(color_cells) < 2:
        errs.append(f"expected ≥2 distinct non-bg colors; found {sorted(color_cells)}")
        return errs
    for color, cells in color_cells.items():
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times; expected exactly 2")
        else:
            (r1, c1), (r2, c2) = cells
            if r1 == r2:
                errs.append(f"color {color} pair shares row {r1} (degenerate rect)")
            if c1 == c2:
                errs.append(f"color {color} pair shares col {c1} (degenerate rect)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n_pairs = rng.randint(2, 3)
    colors = list(random_palette(rng, n_pairs))
    used = set()
    for color in colors:
        for _ in range(100):
            r1, r2 = rng.sample(range(h), 2)
            c1, c2 = rng.sample(range(w), 2)
            pair = {(r1, c1), (r2, c2)}
            if pair & used:
                continue
            used |= pair
            g[r1][c1] = color
            g[r2][c2] = color
            break
        else:
            raise RuntimeError("could not place a non-overlapping color pair")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # only singletons → no color has exactly 2 cells, no rectangles to draw
        g[2][3] = 4
        g[5][7] = 6
        return g
    if name == "single_pair_aligned":
        # pair shares row → "non-degenerate rectangle" fails (rectangle is a line)
        g[3][2] = 4; g[3][7] = 4
        return g
    if name == "pair_too_close":
        # pair adjacent → rectangle is 1x2, border is the pair itself (no signal)
        g[3][2] = 4; g[4][3] = 4
        return g
    return g
