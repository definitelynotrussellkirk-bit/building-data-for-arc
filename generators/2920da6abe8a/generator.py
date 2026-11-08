"""Generator for 8b28cd80.

Rule: 3x3 grid with one marker; rule outputs a fixed 9x9 pattern in the
marker color.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors,
marker_position.
Degenerates: no_marker, two_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2920da6abe8a"
VERSION = "2.0.1"
TASK_ID = "2920da6abe8a"
SUMMARY = (
    "Exactly 3×3 input grid with ONE non-zero MARKER cell at "
    "position (mr, mc) ∈ {0..2}×{0..2}, in any color 1..9. "
    "All other 8 cells are 0. Rule: lookup a 9×9 binary "
    "PATTERN keyed by (mr, mc) — one of 9 hardcoded patterns, "
    "each a concentric-rectangle / nested-frame shape "
    "originating from the corresponding corner/edge of the "
    "input position. The 1-cells in the pattern become the "
    "marker's color; the 0-cells stay 0. Output: 9×9 grid in "
    "the marker color showing the nested-frame fractal."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is exactly 3x3",
    "exactly one non-zero cell at some (mr, mc) in {0..2}×{0..2}",
    "marker color is any of {1..9}",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marker", "two_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "3", "valid": "3"},
    "grid_w":         {"type": "int", "default": "3", "valid": "3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "marker_position":{"type": "str", "default": "rng", "valid": "any9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 3×3 grid with exactly one non-zero marker cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_marker", "two_markers", "full_grid"):
        return []
    errs = []
    if h != 3 or w != 3:
        errs.append(f"expected 3×3 grid, got {h}×{w}")
    else:
        nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
        if nonzero != 1:
            errs.append(f"expected exactly 1 non-zero cell, found {nonzero}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    palette = ctx.draw_distinct_colors("palette", n=1, exclude={0})

    g = full_grid(3, 3, 0)
    mr = rng.randint(0, 2)
    mc = rng.randint(0, 2)
    g[mr][mc] = palette[0]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(3, 3, 0)
    if name == "no_marker":
        return g
    if name == "two_markers":
        g[0][0] = 3
        g[2][2] = 4
        return g
    if name == "full_grid":
        for r in range(3):
            for c in range(3):
                g[r][c] = 3
        return g
    return g
