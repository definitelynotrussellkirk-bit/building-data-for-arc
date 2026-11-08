"""Generator for arc_puzzle_bank_21_set9_e:easy_i06.

Rule: keep colors whose total cell count is even.

Combinatorial axes (8): grid_h, grid_w, palette_kind, even_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_even, all_odd, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49f7c594f382"
VERSION = "1.1.1"
TASK_ID = "49f7c594f382"
SUMMARY = "Keep colors whose total cell count is even."

INVARIANTS = [
    "background is 0",
    "some colors appear an even number of times",
    "some colors appear an odd number of times",
    "output erases odd-count colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_even", "all_odd", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "even_colors":    {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _place(g, rng, color, count):
    h, w = len(g), len(g[0])
    cells = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
    for r, c in rng.sample(cells, count):
        g[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 7, 8)
        even_colors = ctx.draw_int("even_colors", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
        even_colors = ctx.draw_int("even_colors", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        even_colors = ctx.draw_int("even_colors", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], even_colors + 3)
    for color in palette[:even_colors]:
        _place(g, rng, color, rng.choice([2, 4]))
    for color in palette[even_colors:]:
        _place(g, rng, color, rng.choice([1, 3]))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "all_even":
        # all colors have even counts → rule keeps everything, output equals input
        for color, cnt in [(3, 4), (5, 2), (7, 4)]:
            cells = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
            cells = cells[:cnt]
            for r, c in cells:
                g[r][c] = color
        return g
    if name == "all_odd":
        # all colors have odd counts → rule erases everything, output is all-zero
        for color, cnt in [(3, 1), (5, 3), (7, 1)]:
            cells = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
            cells = cells[:cnt]
            for r, c in cells:
                g[r][c] = color
        return g
    if name == "no_cells":
        # empty grid → no colors to count, rule no-op
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=2 distinct non-0 colors; at least one color has an even count."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 2:
        errors.append(f"expected >=2 distinct non-0 colors, found {len(counts)}")
        return errors
    even_colors = [c for c, cnt in counts.items() if cnt % 2 == 0]
    if not even_colors:
        errors.append("no color has an even count (rule would erase everything)")
    return errors
