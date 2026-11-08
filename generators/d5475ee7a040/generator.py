"""Generator for arc_additional_puzzle_bank_volume5:E35.

Rule: nonzero cells are copied to their transposed coordinates without
clearing originals.

Combinatorial axes (8): grid_h/w, grid_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, on_diagonal, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5475ee7a040"
VERSION = "2.1.0"  # add transpose-copy self_check
TASK_ID = "d5475ee7a040"
SUMMARY = (
    "Square 0-bg grid (n×n, n~6-9) with 3 single-cell "
    "MARKERS in distinct colors placed off the main "
    "diagonal at positions (0, 2), (1, n-2), (n-3, 1). "
    "Rule: for every cell (r, c) with input != 0, ALSO "
    "paint the TRANSPOSED position (c, r) with the same "
    "color (keeping the original cell as well). Cells "
    "already on the main diagonal don't move (since "
    "(r, r) == (r, r)). Net: every off-diagonal mark "
    "gets mirrored across the main diagonal, doubling "
    "the non-bg cell count."
)

INVARIANTS = [
    "grid is square",
    "nonzero cells begin off the main diagonal",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "on_diagonal", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_size":      {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
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
        n = ctx.draw_int("grid_size", 6, 7)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_size", 8, 9)
    else:
        n = ctx.draw_int("grid_size", 6, 9)
    colors = list(ctx.draw_distinct_colors("colors", n=3, exclude=[0]))
    g = full_grid(n, n, 0)
    for r, c, color in [
        (0, 2, colors[0]),
        (1, n - 2, colors[1]),
        (n - 3, 1, colors[2]),
    ]:
        g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid is empty or not a 2D list"]
    h, w = len(grid), len(grid[0])
    if h != w:
        return [f"grid is {h}x{w}; expected square"]
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    pts = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    errs = []
    if len(pts) < 3:
        errs.append(f"only {len(pts)} nonzero marker(s); expected at least 3")
    colors = [v for _r, _c, v in pts]
    if len(colors) != len(set(colors)):
        errs.append("marker colors are not distinct")
    visible_copies = 0
    for r, c, _v in pts:
        if r == c:
            errs.append(f"marker at ({r},{c}) lies on the main diagonal and will not visibly copy")
        elif grid[c][r] == 0:
            visible_copies += 1
    if visible_copies == 0:
        errs.append("no marker has an empty transposed destination; output would hide the copy rule")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_marks":
        return g
    if name == "on_diagonal":
        for i in range(7):
            g[i][i] = 3
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 3
        return g
    return g
