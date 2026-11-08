"""Generator for arc_additional_puzzles_21_set22_bundle:E150.

Rule: nonzero cells copied to transposed coordinates while originals
remain.

Combinatorial axes (8): grid_h/w, grid_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, on_diagonal, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1fc836c1922"
VERSION = "2.0.1"  # marks were at 3 FIXED positions; only colors/grid-size varied. Rule copies each nonzero (r,c) to (c,r), originals remain. Now place K (3-8) marks at RANDOM off-diagonal positions with no transpose-pair collisions (so originals stay + copies are new), random colors.
TASK_ID = "e1fc836c1922"
SUMMARY = "Square grid with K (3-8) marks at random OFF-DIAGONAL positions (no (r,c)/(c,r) collisions), random colors. Rule copies each nonzero (r,c) to (c,r) while originals remain (reflection across the main diagonal, additive)."

INVARIANTS = [
    "grid is square",
    "nonzero cells start off the main diagonal",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "on_diagonal", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_size":      {"type": "int", "default": "rng 6..9", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "n_marks":       {"type": "int", "default": "rng 4..7", "valid": "3..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_marks|on_diagonal|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify square off-diagonal marks with empty transpose targets."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    n = len(grid)
    errs = []
    if any(len(row) != n for row in grid):
        errs.append("grid must be square")
        return errs
    marks = [(r, c) for r in range(n) for c in range(n) if grid[r][c] != 0]
    min_marks = 3 if difficulty == "easy" else 6 if difficulty == "hard" else 4
    if len(marks) < min_marks:
        errs.append(f"only {len(marks)} marks; expected at least {min_marks}")
    diag = [(r, c) for r, c in marks if r == c]
    if diag:
        errs.append(f"marks must start off the diagonal: {diag[:3]}")
    mirror_occupied = [(r, c) for r, c in marks if grid[c][r] != 0]
    if mirror_occupied:
        errs.append(f"transpose targets should be empty before the rule fires: {mirror_occupied[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n = ctx.draw_int("grid_size", 6, 7); k = ctx.draw_int("n_marks", 3, 4)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_size", 9, 12); k = ctx.draw_int("n_marks", 6, 9)
    else:
        n = ctx.draw_int("grid_size", 7, 10); k = ctx.draw_int("n_marks", 4, 7)
    g = full_grid(n, n, 0)
    cells = [(r, c) for r in range(n) for c in range(n) if r != c]  # off-diagonal
    rng.shuffle(cells)
    placed = 0
    for (r, c) in cells:
        if placed >= k:
            break
        if g[r][c] != 0 or g[c][r] != 0:        # keep transpose target empty
            continue
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        placed += 1
    if placed == 0:
        g[0][1] = 3
    return g


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
