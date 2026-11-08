"""Generator for arc_puzzle_bank_21_set8:easy_h06.

Rule: add a gray one-step down-right shadow behind every nonzero cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, marks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marks, marks_at_bottom_right, shadow_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f525a2f470f1"
VERSION = "1.4.0"  # bigger grids + more marks (already clean: excludes 5, exercises bounds branch)
TASK_ID = "f525a2f470f1"
SUMMARY = "For every nonzero cell, paint gray(5) at (r+1, c+1) if that cell is bg."

# Rivals: 'shadow up-left' refuted by ≥1 demo with marks where down-right
# is bg but up-left is not. 'replace with gray (not add)' refuted by any
# demo (original cells preserved). 'use mark's color for shadow' refuted
# by any demo (shadow is always 5). 'shadow distance 2' refuted by ≥2
# demos where row+1/col+1 vs row+2/col+2 differ.
# 4 demos with varied mark colors + positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "input marks are sparse",
    "shadow target cells are initially background",
    "original nonzero cells are preserved",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marks", "marks_at_bottom_right", "shadow_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "marks":          {"type": "int", "default": "rng 3..5", "valid": "1..16"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "interior_with_shadow_room",
                       "valid": "interior_with_shadow_room"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_marks|marks_at_bottom_right|shadow_already_filled"},
}


def _can_place_mark(g, r, c, *, require_shadow_room=True):
    """Return True iff a default mark can be placed at (r,c).

    The default stream is supposed to demonstrate the normal branch where every
    interior mark has an initially blank down-right target. The previous helper
    only checked the candidate's own down-right cell; a later mark could still be
    placed *on* an earlier mark's target (the up-left relation), leaking the
    `shadow_already_filled` degenerate texture into default episodes.
    """
    h, w = len(g), len(g[0])
    if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
        return False
    # Do not occupy an existing mark's down-right target.
    if r > 0 and c > 0 and g[r - 1][c - 1] != 0:
        return False
    if require_shadow_room:
        rr, cc = r + 1, c + 1
        if not (0 <= rr < h and 0 <= cc < w) or g[rr][cc] != 0:
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 6, 9)
        target = ctx.draw_int("marks", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 20)
        w = ctx.draw_int("grid_w", 14, 24)
        target = ctx.draw_int("marks", 8, 16)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 9, 16)
        target = ctx.draw_int("marks", 4, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    # Mark colors exclude 5 (reserved for shadow) and 0 (bg).
    mark_pool = [1, 2, 3, 4, 6, 7, 8, 9]
    for _ in range(240):
        if placed >= target:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if _can_place_mark(g, r, c, require_shadow_room=True):
            g[r][c] = rng.choice(mark_pool)
            placed += 1
    # Some marks on the bottom row / right column (no shadow target).
    # These exercise the rule's bounds check.
    n_edge = rng.randint(0, 2) if difficulty != "easy" else 0
    for _ in range(40):
        if n_edge <= 0:
            break
        side = rng.choice(["bottom", "right"])
        if side == "bottom":
            r = h - 1; c = rng.randint(0, w - 1)
        else:
            r = rng.randint(0, h - 1); c = w - 1
        if _can_place_mark(g, r, c, require_shadow_room=False):
            g[r][c] = rng.choice(mark_pool)
            n_edge -= 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_marks":
        # blank grid → no cells to shadow, rule is identity
        return g
    if name == "marks_at_bottom_right":
        # marks on bottom row or right column → no down-right cell exists, rule is identity
        g[h - 1][2] = 4; g[h - 1][6] = 6
        g[2][w - 1] = 3; g[5][w - 1] = 8
        return g
    if name == "shadow_already_filled":
        # mark + non-zero cell at down-right → shadow target is occupied, rule's paint clobbers it
        g[1][1] = 4; g[2][2] = 7   # already 7 (gray-ish), would get overwritten
        g[3][4] = 6; g[4][5] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Assert the default input actually teaches the normal down-right shadow rule."""
    errs = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    marks = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not marks:
        errs.append("default grid must contain at least one mark")
    if any(v == 5 for _, _, v in marks):
        errs.append("input mark colors must exclude 5, which is reserved for shadows")
    interior = [(r, c, v) for r, c, v in marks if r + 1 < h and c + 1 < w]
    if not interior:
        errs.append("default grid must include at least one mark with a down-right target")
    for r, c, _ in interior:
        if grid[r + 1][c + 1] != 0:
            errs.append("interior marks must have an initially blank down-right shadow target")
            break
    return errs
