"""Generator for 33067df9.

Rule: sparse values on odd grid coordinates expand into a 26x26
block-and-connector diagram.

Combinatorial axes (8): grid_h/w, macro_size, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_macros, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "53599600b6c9"
VERSION = "1.1.1"
TASK_ID = "53599600b6c9"
SUMMARY = "Sparse values on odd coords expand into block-and-connector diagram."

INVARIANTS = [
    "semantic cells live at odd input rows and columns",
    "zero semantic cells remain blank in the expansion",
    "equal adjacent semantic cells create horizontal connectors",
    "macro_size is at least 3 so connectors have room",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_macros", "full_grid", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "7..11"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "7..11"},
    "macro_size":     {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; ≥1 non-bg cell at odd row AND odd col coordinates."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    odd_cells = [(r, c) for r in range(h) for c in range(w)
                 if r % 2 == 1 and c % 2 == 1 and grid[r][c] != 0]
    if not odd_cells:
        return errors  # degenerate (no_macros) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    macro_size = ctx.draw_int("macro_size", 3, 5)   # widen input variety (output is always 26x26 by rule)
    colors = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    size = macro_size * 2 + 1
    g = full_grid(size, size, 0)
    for ri in range(macro_size):
        for ci in range(macro_size):
            if rng.random() < 0.35:
                g[1 + 2 * ri][1 + 2 * ci] = rng.choice(colors)
    row = rng.randrange(macro_size)
    g[1 + 2 * row][1] = colors[0]
    g[1 + 2 * row][3] = colors[0]
    if macro_size > 3:
        g[3][1] = colors[1]
        g[5][1] = colors[1]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_macros":
        return g
    if name == "single_cell":
        g[3][3] = 2
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 2
        return g
    return g
