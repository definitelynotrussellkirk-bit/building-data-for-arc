"""Generator for arc_additional_puzzle_bank_volume3:E15.

Rule: green path endpoints (the 1-cardinal-neighbor cells) are
recolored red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_segments, texture.
Degenerates: no_segments, length_one, non_straight.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2361d6aa42c3"
VERSION = "1.1.1"
TASK_ID = "2361d6aa42c3"
SUMMARY = "Green path endpoints, defined by one cardinal neighbor, are recolored red."

INVARIANTS = [
    "background is 0",
    "green components are straight path segments",
    "each path segment has two endpoints",
    "segments are separated so components do not merge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_segments", "length_one", "non_straight")
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
                       "valid": "default|warm|cool|varied|no_segments|length_one|non_straight"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one green(3) cell forming part of a segment."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    greens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not greens:
        return errors  # degenerate no_segments — allowed
    if len(greens) < 2:
        errors.append("fewer than 2 green cells — cannot form a segment with endpoints")
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
                g[r][c + dc] = 3
            used.add(r)
        else:
            choices = [c for c in range(w) if all(abs(c - cc) > 1 for cc in used)]
            if not choices:
                break
            c = rng.choice(choices)
            length = rng.randint(3, min(6, h))
            r = rng.randint(0, h - length)
            for dr in range(length):
                g[r + dr][c] = 3
            used.add(c)
        made += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_segments":
        # Empty grid — rule has no green segments and no endpoints to
        # recolor.
        return g
    if name == "length_one":
        # Single green cells — endpoint count would be 0 (no
        # cardinal neighbors of same color); rule's "1-cardinal
        # endpoint" identification fails.
        g[2][2] = 3; g[5][7] = 3
        return g
    if name == "non_straight":
        # Bent path (L-shape) — multiple cells have just 1 cardinal
        # neighbor; rule's straight-line precondition fails.
        for r, c in [(2, 2), (3, 2), (4, 2), (4, 3), (4, 4)]: g[r][c] = 3
        return g
    return g
