"""Generator for 39e1d7f9.

Rule: a separator grid propagates the strongest local macro-cell
neighborhood pattern.

Combinatorial axes (8): grid_h/w, cell_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_targets, no_support, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bfe6770672a2"
RULE_HASH = "2b582e94a5f7"  # canonical rule this generator was written against
VERSION = "2.1.1"
TASK_ID = "bfe6770672a2"
SUMMARY = (
    "Grid laid out as a 4×4 MACRO-GRID of cell_size × "
    "cell_size (cell_size ∈ {1, 2}) macro-cells, "
    "separated by SEPARATOR rows/cols painted color "
    "`sep` (drawn from non-bg). Each macro-cell is one "
    "of: TARGET color, SUPPORT color, or empty. The "
    "input is configured so one TARGET macro-cell at "
    "(1, 1) has a distinctive SUPPORT neighborhood "
    "(its 4 cardinal macro-cells colored support); "
    "other TARGET macro-cells appear elsewhere without "
    "support. Rule: detect the target-color macro-cell "
    "with the strongest support neighborhood. "
    "Propagate that pattern (paint matching support "
    "neighbors) to every other target macro-cell."
)

INVARIANTS = [
    "full separator rows and columns split the grid into macro-cells",
    "one target-colored macro-cell has a distinctive colored neighbor pattern",
    "other target macro-cells receive that same neighbor pattern where cells are blank",
]

CELL_KINDS = ("c1", "c2")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_targets", "no_support", "full_grid")
HELPFUL_TEXTURES = CELL_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varied", "valid": "varied"},
    "grid_w":         {"type": "int", "default": "varied", "valid": "varied"},
    "cell_size":      {"type": "int", "default": "rng helpful",
                       "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for cell_size",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has full separator rows and columns (same non-zero color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    # Find full-width rows that are all same non-zero value (separators)
    full_rows = [r for r in range(h) if len({grid[r][c] for c in range(w)}) == 1 and grid[r][0] != 0]
    full_cols = [c for c in range(w) if len({grid[r][c] for r in range(h)}) == 1 and grid[0][c] != 0]
    if not full_rows:
        errs.append("no full-width separator rows found")
    if not full_cols:
        errs.append("no full-height separator columns found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    tx = overrides.get("texture")
    if tx in CELL_KINDS:
        cell = int(tx[1])
    elif difficulty == "easy":
        cell = ctx.draw_int("cell_size", 1, 2)
    elif difficulty == "hard":
        cell = ctx.draw_int("cell_size", 4, 6)
    else:
        cell = ctx.draw_int("cell_size", 1, 5)
    sep, target, support = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    macro_h = 4
    macro_w = 4
    h = macro_h * cell + (macro_h - 1)
    w = macro_w * cell + (macro_w - 1)
    g = full_grid(h, w, 0)
    for r in range(cell, h, cell + 1):
        for c in range(w):
            g[r][c] = sep
    for c in range(cell, w, cell + 1):
        for r in range(h):
            g[r][c] = sep

    def fill_macro(i, j, color):
        r0 = i * (cell + 1)
        c0 = j * (cell + 1)
        for r in range(r0, r0 + cell):
            for c in range(c0, c0 + cell):
                g[r][c] = color

    fill_macro(1, 1, target)
    fill_macro(0, 1, support)
    fill_macro(1, 0, support)
    fill_macro(1, 2, support)
    fill_macro(2, 1, support)
    fill_macro(2, 3, target)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_targets":
        for r in range(1, 7, 2):
            for c in range(7):
                g[r][c] = 5
        for c in range(1, 7, 2):
            for r in range(7):
                g[r][c] = 5
        return g
    if name == "no_support":
        g[0][0] = 3
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 5
        return g
    return g
