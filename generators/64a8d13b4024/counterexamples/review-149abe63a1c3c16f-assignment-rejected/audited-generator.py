"""Generator for arc_additional_puzzle_bank_volume9:H61 — Bar chart of color counts.

Rule: count cells of colors 1, 2, 3. Build a 6×3 grid where column c
(0..2) is filled from the bottom up to height = count[c+1], using
color c+1.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n1, n2, n3,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_color, all_equal, count_overflow.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "64a8d13b4024"
VERSION = "1.1.1"
TASK_ID = "64a8d13b4024"
SUMMARY = "Scattered cells of colors 1,2,3; output is 6x3 bar chart of their counts."

INVARIANTS = [
    "between 1 and 6 cells of color 1",
    "between 1 and 6 cells of color 2",
    "between 1 and 6 cells of color 3",
    "the three counts must NOT all be equal (else output is uniform — degenerate)",
    "input grid is roomy (≥9x9) so cells can scatter",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_color", "all_equal", "count_overflow")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n1":             {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "n2":             {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "n3":             {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 cell each of colors 1, 2, and 3 (unless degenerate)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    for c, name in [(1, "color-1"), (2, "color-2"), (3, "color-3")]:
        if not any(grid[r][cc] == c for r in range(h) for cc in range(w)):
            errs.append(f"no {name} cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n1 = ctx.draw_int("n1", 1, 3)
        n2 = ctx.draw_int("n2", 1, 3)
        n3 = ctx.draw_int("n3", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n1 = ctx.draw_int("n1", 4, 6)
        n2 = ctx.draw_int("n2", 4, 6)
        n3 = ctx.draw_int("n3", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n1 = ctx.draw_int("n1", 1, 6)
        n2 = ctx.draw_int("n2", 1, 6)
        n3 = ctx.draw_int("n3", 1, 6)
    if n1 == n2 == n3:
        n3 = (n3 % 6) + 1

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("placements")
    positions = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(positions)
    cursor = 0

    def place(n, color):
        nonlocal cursor
        placed = 0
        while placed < n and cursor < len(positions):
            r, c = positions[cursor]
            cursor += 1
            if g[r][c] == 0:
                g[r][c] = color
                placed += 1

    place(n1, 1)
    place(n2, 2)
    place(n3, 3)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "missing_color":
        # only colors 1 and 3 (color 2 has zero cells) → bar 2 is empty in output
        for (r, c) in [(1, 2), (3, 5), (5, 1)]: g[r][c] = 1
        for (r, c) in [(2, 8), (4, 4), (6, 7), (8, 2)]: g[r][c] = 3
        return g
    if name == "all_equal":
        # n1 == n2 == n3 → all 3 bars equal height → output is a uniform 3-color rectangle
        for (r, c) in [(1, 1), (2, 3), (3, 5)]: g[r][c] = 1
        for (r, c) in [(1, 7), (4, 2), (5, 8)]: g[r][c] = 2
        for (r, c) in [(7, 1), (7, 4), (8, 6)]: g[r][c] = 3
        return g
    if name == "count_overflow":
        # any count > 6 → bar can't fit in the 6-row output (rule clamps or breaks)
        for r in range(8):
            for c in range(2):
                g[r][c] = 1
        g[0][6] = 2; g[1][6] = 2
        g[5][8] = 3
        return g
    return g
