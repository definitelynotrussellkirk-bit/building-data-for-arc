"""Generator for arc_additional_puzzles_21_set5:E29.

Rule: each red anchor keeps value 2 and stamps orange 7 to its diagonal
neighbors.

Combinatorial axes (8): grid_h/w, n_anchors, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_anchors, single_anchor, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "abbeda7fe821"
VERSION = "2.0.1"
TASK_ID = "abbeda7fe821"
SUMMARY = (
    "0-bg grid (h, w ~6-10) with 2-4 isolated color-2 "
    "(red) ANCHOR cells placed at well-spaced positions "
    "(rows/cols at multiples of 3, so halos don't "
    "conflict). Rule: for each color-2 anchor at (r, c), "
    "KEEP the anchor at value 2, and PAINT each of its 4 "
    "DIAGONAL neighbors (r±1, c±1) with color 7 (orange). "
    "Cardinal neighbors stay 0. Net: each red anchor "
    "grows into a 5-cell X pattern — red center + orange "
    "diagonal halo."
)
INVARIANTS = [
    "anchors are red",
    "anchors are spaced so halos do not conflict",
    "background is zero",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_anchors", "single_anchor", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "6..10"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "6..10"},
    "n_anchors":      {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one color-2 (red) anchor cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_anchors",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_red = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_red:
        errs.append("no color-2 (red) anchor cells found")
    has_non_anchor = any(grid[r][c] not in (0, 2) for r in range(h) for c in range(w))
    if has_non_anchor:
        errs.append("unexpected non-zero non-anchor colors in input")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 6, 10)
    n = ctx.draw_int("n_anchors", 2, 4)
    g = full_grid(h, w, 0)
    spots = [(r, c) for r in range(1, h - 1, 3) for c in range(1, w - 1, 3)]
    rng.shuffle(spots)
    for r, c in spots[:n]:
        g[r][c] = 2
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "no_anchors":
        return g
    if name == "single_anchor":
        g[3][3] = 2
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 2
        return g
    return g
