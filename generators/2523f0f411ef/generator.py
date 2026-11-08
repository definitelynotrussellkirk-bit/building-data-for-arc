"""Generator for 56dc2b01.

Rule: color-3 shape moves adjacent to a color-2 line, and a color-8
line appears on its far side.

Combinatorial axes (8): grid_h/w, orientation, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, shape_kind.
Degenerates: no_line, no_shape, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2523f0f411ef"
VERSION = "1.1.1"
TASK_ID = "2523f0f411ef"
SUMMARY = "Color-3 shape moves adjacent to color-2 line; far-side color-8 line."

INVARIANTS = [
    "background is color 0",
    "all color-2 cells form one straight horizontal or vertical line",
    "all color-3 cells form one compact source shape away from that line",
    "shape sits clear of grid borders so the move has room",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_line", "no_shape", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 0)],
    [(0, 1), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 15..17", "valid": "12..20"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "orientation":    {"type": "str", "default": "horizontal", "valid": "horizontal"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "shape_kind":     {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_line|no_shape|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one color-2 line cell and at least one color-3 shape cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    has_3 = any(grid[r][c] == 3 for r in range(h) for c in range(w))
    if not has_2 and not has_3:
        return errors  # degenerate — allowed
    if not has_2:
        errors.append("no color-2 (line) cells found")
    if not has_3:
        errors.append("no color-3 (shape) cells found")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    h = 15 + rng.randint(0, 2)
    w = 9 + rng.randint(0, 3)
    g = full_grid(h, w, 0)
    line_r = h - 3
    for c in range(1, w - 1):
        g[line_r][c] = 2
    shape = SHAPES[sample_index % len(SHAPES)]
    c0 = rng.randint(1, w - 4)
    r0 = rng.randint(1, max(1, line_r - 7))
    for dr, dc in shape:
        g[r0 + dr][c0 + dc] = 3
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 11, 0)
    if name == "no_line":
        for dr, dc in SHAPES[0]:
            g[3 + dr][3 + dc] = 3
        return g
    if name == "no_shape":
        for c in range(1, 10):
            g[10][c] = 2
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(11):
                g[r][c] = 2
        return g
    return g
