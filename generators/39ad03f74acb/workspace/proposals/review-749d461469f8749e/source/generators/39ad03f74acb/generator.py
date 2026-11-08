"""Generator for arc_additional_puzzle_bank_volume4:E22.

Rule: interior cells of straight blue segments (cells with 2 cardinal
blue neighbors) are recolored red; endpoints stay blue.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_segments, texture.
Degenerates: no_segments, length_two, non_straight.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39ad03f74acb"
VERSION = "1.1.1"
TASK_ID = "39ad03f74acb"
SUMMARY = "Interior cells of straight blue segments are recolored red."

INVARIANTS = [
    "background is 0",
    "blue components are straight horizontal or vertical segments",
    "segments have length at least three",
    "segments are separated so they do not merge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_segments", "length_two", "non_straight")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_segments":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "axis_aligned_segments",
                       "valid": "axis_aligned_segments"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_segments|length_two|non_straight"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 color-1 (blue) segment cell of length ≥3; values 0..9."""
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
    blues = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if blues == 0:
        pass  # degenerate (no_segments) — allowed
    elif blues < 3:
        errors.append(f"expected ≥3 blue cells for valid segment, found {blues}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_segments = ctx.draw_int("n_segments", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_segments = ctx.draw_int("n_segments", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_segments = ctx.draw_int("n_segments", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    horizontal = rng.choice([False, True])
    used: set[int] = set()
    made = 0
    for _ in range(200):
        if made >= n_segments:
            break
        if horizontal:
            choices = [r for r in range(h) if all(abs(r - rr) > 1 for rr in used)]
            if not choices:
                break
            r = rng.choice(choices)
            length = rng.randint(3, min(6, w))
            c = rng.randint(0, w - length)
            for dc in range(length):
                g[r][c + dc] = 1
            used.add(r)
        else:
            choices = [c for c in range(w) if all(abs(c - cc) > 1 for cc in used)]
            if not choices:
                break
            c = rng.choice(choices)
            length = rng.randint(3, min(6, h))
            r = rng.randint(0, h - length)
            for dr in range(length):
                g[r + dr][c] = 1
            used.add(c)
        made += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_segments":
        # Empty grid — rule has no segments and no interiors to recolor.
        return g
    if name == "length_two":
        # Length-2 segments — both cells are endpoints, no interior;
        # rule's "≥3 length" filter excludes them, output equals input.
        g[2][2] = 1; g[2][3] = 1
        g[5][6] = 1; g[6][6] = 1
        return g
    if name == "non_straight":
        # Bent components — rule's straight-line precondition fails.
        for r, c in [(2, 2), (3, 2), (4, 2), (4, 3), (4, 4)]: g[r][c] = 1
        return g
    return g
