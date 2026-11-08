"""Generator for arc_puzzle_bank_21_set8:easy_h01 — keep midpoint of odd-length runs.

Rule: keep only the midpoint of each odd-length horizontal run.

Combinatorial axes (8): grid_h, grid_w, palette_kind, runs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: even_length_runs, no_runs, length_1_runs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "579e2cb85781"
VERSION = "1.1.1"
TASK_ID = "579e2cb85781"
SUMMARY = "Keep only the midpoint of each odd-length horizontal run."

INVARIANTS = [
    "background is 0",
    "active rows contain odd-length same-color runs",
    "runs have length at least 3",
    "output erases every run cell except its midpoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("even_length_runs", "no_runs", "length_1_runs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "runs":           {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "odd_length_horiz_runs",
                       "valid": "odd_length_horiz_runs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("runs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 10, 11)
        target = ctx.draw_int("runs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 11)
        target = ctx.draw_int("runs", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(160):
        if placed >= target:
            break
        length = rng.choice([3, 5])
        if length > w:
            length = 3
        r = rng.randrange(h)
        c = rng.randint(0, w - length)
        if any(g[r][cc] != 0 for cc in range(max(0, c - 1), min(w, c + length + 1))):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for cc in range(c, c + length):
            g[r][cc] = color
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one odd-length (>=3) horizontal run of same color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    found = False
    for r in range(h):
        c = 0
        while c < w:
            v = grid[r][c]
            if v != 0:
                end = c + 1
                while end < w and grid[r][end] == v:
                    end += 1
                length = end - c
                if length >= 3 and length % 2 == 1:
                    found = True
                c = end
            else:
                c += 1
    if not found:
        errs.append("no odd-length (>=3) horizontal run found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "even_length_runs":
        # all runs even-length → no unique midpoint cell
        for c in range(1, 5): g[1][c] = 4   # length 4
        for c in range(2, 8): g[3][c] = 6   # length 6
        return g
    if name == "no_runs":
        # blank → no runs to reduce
        return g
    if name == "length_1_runs":
        # all length-1 → midpoint is the cell itself, rule has no observable effect
        g[1][3] = 4
        g[3][6] = 6
        g[4][1] = 3
        return g
    return g
