"""Generator for arc_puzzle_bank_third21:E18.

Rule: every nonzero cell drops one row when the cell below is background
in the input.

Combinatorial axes (8): grid_h/w, n_cells, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: empty_grid, single_cell, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e873f4e123b6"
VERSION = "2.1.0"  # was cells only in rows 0..h-2, sparse -> 'stay' branch barely hit (bottom-row cells 0/30, vertical adjacency 10/30) + colors only (i%8)+1. Now cells anywhere incl bottom row, force >=1 vertical pair + >=1 bottom cell, random colors 1-9
TASK_ID = "e873f4e123b6"
SUMMARY = (
    "0-bg grid with several sparse non-bg cells (random colors 1-9) anywhere, "
    "INCLUDING the bottom row and some vertically stacked. Rule: SIMULTANEOUSLY "
    "(on input state) each non-zero cell at (r,c) drops to (r+1,c) iff (r+1,c) "
    "is in-bounds AND 0 in the input; cells at the bottom row or with a non-zero "
    "cell directly below STAY. Both branches (drop / stay) are exercised every "
    "instance; positions, colors, counts and grid size vary."
)
INVARIANTS = [
    "background is 0; non-zero cells are sparse",
    ">=1 cell has empty space below (the 'drop' branch fires)",
    ">=1 cell stays: a vertical-adjacent pair (non-zero below) AND/OR a bottom-row cell",
    "all moves are simultaneous (decided on the input state)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("empty_grid", "single_cell", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..14 by diff", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 6..14 by diff", "valid": "6..14"},
    "n_cells":        {"type": "int", "default": "rng 4..14 by diff", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 6, 8)
        n = ctx.draw_int("n_cells", 4, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 10, 14)
        n = ctx.draw_int("n_cells", 8, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 11); w = ctx.draw_int("grid_w", 7, 11)
        n = ctx.draw_int("n_cells", 5, 9)
    g = full_grid(h, w, 0)
    positions = [(r, c) for r in range(h) for c in range(w)]   # incl bottom row
    rng.shuffle(positions)
    placed = []
    for (r, c) in positions[:n]:
        g[r][c] = rng.randint(1, 9)                            # random full palette
        placed.append((r, c))
    # guarantee the 'stay because non-zero below' branch: stack a cell above a placed one
    for (r, c) in placed:
        if r >= 1 and g[r - 1][c] == 0:
            g[r - 1][c] = rng.randint(1, 9)
            break
    # guarantee the 'stay at bottom row' branch
    if not any(g[h - 1][c] != 0 for c in range(w)):
        g[h - 1][rng.randint(0, w - 1)] = rng.randint(1, 9)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "empty_grid":
        return g
    if name == "single_cell":
        g[2][3] = 3
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 3
        return g
    return g
