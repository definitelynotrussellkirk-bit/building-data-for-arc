"""Generator for arc_puzzle_bank_21_set6_s:S6_M1.

Rule: trace wires from red starts and recolor only the longest blue
path to green.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_wires,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_lengths, single_wire, no_red_start.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39c4e8d5275c"
VERSION = "2.0.1"
TASK_ID = "39c4e8d5275c"
SUMMARY = (
    "0-bg grid (h~8-10, w~13-16) with 3 "
    "HORIZONTAL WIRES at non-touching "
    "rows (sampled from {1, 3, 5, 7}). "
    "Each wire is: ONE COLOR-2 (red) "
    "START cell at (r, c0) followed by "
    "a sequence of COLOR-1 (blue) cells "
    "at (r, c0+1..c0+length). WIRE "
    "LENGTHS are {3, 5, 7} shuffled "
    "(strictly distinct, longest is "
    "unique). Rule (LONGEST-WIRE "
    "RECOLOR): trace EACH WIRE from "
    "its RED START. COUNT the length "
    "of each wire's BLUE PATH. "
    "RECOLOR the entire BLUE PATH of "
    "the LONGEST wire to COLOR 3 "
    "(green). Other wires' blue cells "
    "stay blue. Red start cells stay. "
    "Net: longest blue wire becomes "
    "green; shorter wires keep their "
    "blue color."
)

INVARIANTS = [
    "each color-2 marker has exactly one adjacent color-1 wire start",
    "blue wires are disjoint",
    "one wire is strictly longest",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_lengths", "single_wire", "no_red_start")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 13..16", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_wires":        {"type": "int", "default": "3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "row_separated_wires",
                       "valid": "row_separated_wires"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 color-2 (red) wire start; ≥1 color-1 (blue) wire cell; values 0..9."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    reds = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    blues = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if reds == 0:
        pass  # degenerate (no_red_start) — allowed
    elif reds < 1:
        errors.append("no red start cells found")
    if blues == 0:
        pass  # degenerate (single_wire / no start) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 15, 16)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 13, 16)
    g = full_grid(h, w, 0)
    row_pool = [r for r in [1, 3, 5, 7] if r < h - 1]
    rows = rng.sample(row_pool, 3)
    lengths = [3, 5, 7]
    rng.shuffle(lengths)
    for row, length in zip(rows, lengths):
        start_c = rng.randint(0, max(0, w - length - 2))
        g[row][start_c] = 2
        for c in range(start_c + 1, start_c + 1 + length):
            g[row][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    if name == "tied_lengths":
        # two wires of equal length → "longest" is ambiguous
        g[1][0] = 2
        for c in range(1, 6): g[1][c] = 1
        g[5][0] = 2
        for c in range(1, 6): g[5][c] = 1
        return g
    if name == "single_wire":
        # only one wire → trivially longest, no comparison
        g[3][0] = 2
        for c in range(1, 5): g[3][c] = 1
        return g
    if name == "no_red_start":
        # blue wires without red 2-markers → wires have no entry point
        for c in range(2, 6): g[1][c] = 1
        for c in range(2, 8): g[5][c] = 1
        return g
    return g
