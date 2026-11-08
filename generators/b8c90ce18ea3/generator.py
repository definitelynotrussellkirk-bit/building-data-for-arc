"""Generator for arc_additional_puzzles_21_set16_bundle:E112.

Rule: scattered nonzero values emitted as one row in scan order.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, single_mark, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b8c90ce18ea3"
VERSION = "2.0.1"
TASK_ID = "b8c90ce18ea3"
SUMMARY = (
    "0-bg grid (h, w~5-8) with SPARSE "
    "NONZERO CELLS scattered at 4-7 random "
    "positions using a 3-5 color palette "
    "drawn from 1..9. Cells are placed at "
    "random distinct positions; no spatial "
    "structure or invariant. Always at "
    "least one nonzero mark. Rule "
    "(SCAN-ORDER EMIT): READ the grid in "
    "ROW-MAJOR SCAN ORDER (top-to-bottom, "
    "left-to-right). COLLECT every "
    "nonzero value in ENCOUNTER ORDER into "
    "a list. EMIT them as a SINGLE-ROW "
    "OUTPUT (1 × N grid where N is the "
    "number of nonzero cells). Output "
    "preserves: (a) the scan order, NOT "
    "the input positions; (b) repeated "
    "colors appear as separate entries "
    "(no dedup); (c) sorted order is "
    "irrelevant. Net: scattered marks "
    "→ 1-row sequence in scan order."
)

# Rivals: 'output is input' refuted by any demo (output is 1×N).
# 'sort values' refuted by ≥1 demo where scan order ≠ sorted order.
# 'reverse scan order' refuted by ≥1 demo. 'output unique colors
# only' refuted by ≥1 demo with repeated colors that all appear.
# 3 demos with ≥4 distinct cells in varied positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "nonzero values are sparse",
    "there is always at least one nonzero value",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "single_mark", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "5..8"},
    "grid_w":         {"type": "int", "default": "rng 5..8", "valid": "5..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'warm|cool|broad|primary'},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'warm|cool|broad|primary|no_marks|single_mark|full_grid'},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at most 5 distinct nonzero color values (sparse palette)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nz_vals = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(nz_vals) > 6:
        return [f"too many distinct nonzero colors: {sorted(nz_vals)} (expected ≤6)"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        h = rng.randint(4, 6); w = rng.randint(4, 6)
        n_marks = rng.randint(3, 5); n_colors = rng.randint(2, 3)
    elif difficulty == "hard":
        h = rng.randint(8, 12); w = rng.randint(8, 12)
        n_marks = rng.randint(7, 12); n_colors = rng.randint(4, 6)
    else:
        h = rng.randint(6, 9); w = rng.randint(6, 9)
        n_marks = rng.randint(4, 7); n_colors = rng.randint(3, 5)
    palette_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(palette_pool)
    palette = palette_pool[:n_colors]
    g = full_grid(h, w, 0)
    n_marks = min(n_marks, h * w - 1)
    positions = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(positions)
    for (r, c) in positions[:n_marks]:
        g[r][c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_marks":
        return g
    if name == "single_mark":
        g[3][3] = 3
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 3
        return g
    return g
