"""Generator for arc_puzzle_bank_ninth21:H59 — 4-fold rotation about a 9-pivot.

Rule (re-derived from the canonical solution; the old 'find matching pair across
6 panels' summary was WRONG): take the FIRST color-9 cell as a PIVOT. For every
non-0/non-9 colored cell, stamp it (in its color) at all FOUR 90-degree
rotations of its offset about the pivot (0/90/180/270), clipping out-of-bounds
copies. The output is a fresh grid holding the 9 pivot plus the 4-fold
rotational orbit of every colored cell.

Combinatorial axes: grid size, pivot position, number of colored cells, their
colors and positions.
Degenerates: no_pivot, pivot_only, cells_no_pivot.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fa4348bba82b"
VERSION = "3.0.0"  # rewrite to the REAL rule (4-fold rotation about the 9-pivot); old panel/find-pair model was wrong & exercised 4 shapes
TASK_ID = "fa4348bba82b"

SUMMARY = (
    "Grid (size varies) with ONE color-9 (maroon) PIVOT cell and 1-8 other "
    "colored cells (colors 1-8) scattered around it. Rule: take the (first) "
    "color-9 cell as the PIVOT. For EACH non-0/non-9 colored cell, compute its "
    "offset from the pivot and stamp the cell (keeping its color) at all FOUR "
    "90-degree ROTATIONS of that offset about the pivot — 0, 90, 180 and 270 "
    "degrees — dropping any copy that falls outside the grid. OUTPUT a fresh "
    "grid containing the 9 pivot plus the 4-fold rotational orbit of every "
    "colored cell. Net: the scattered cells are completed into a "
    "4-fold-rotationally-symmetric pattern around the maroon pivot."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-9 pivot cell",
    "1-8 colored cells in colors 1-8 (not 0, not 9), none on the pivot",
    "the pivot is interior enough that at least one cell's rotations stay in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pivot", "pivot_only", "cells_no_pivot")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-11 easy / 10-16 med / 14-24 hard", "valid": "5..28"},
    "grid_w":         {"type": "int", "default": "7-11 easy / 10-16 med / 14-24 hard", "valid": "5..28"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "1-3 easy / 2-5 med / 4-8 hard", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 1..8", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "cells_around_pivot",
                       "valid": "cells_around_pivot"},
    "n_distinct_colors": {"type": "int", "default": "up to 8", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _orbit_in_bounds(pr, pc, r, c, h, w):
    """Do any of the 4 rotations of (r,c) about (pr,pc) land in-bounds (other
    than the identity)? Used to ensure the output differs from the input."""
    dr, dc = r - pr, c - pc
    for k in range(1, 4):
        if k == 1:
            o = (-dc, dr)
        elif k == 2:
            o = (-dr, -dc)
        else:
            o = (dc, -dr)
        rr, cc = pr + o[0], pc + o[1]
        if 0 <= rr < h and 0 <= cc < w:
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, nr = (7, 11), (7, 11), (1, 3)
    elif difficulty == "hard":
        hr, wr, nr = (14, 24), (14, 24), (4, 8)
    else:
        hr, wr, nr = (10, 16), (10, 16), (2, 5)

    rng = ctx.draw_rng("layout")
    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        # pivot biased toward the interior so rotations have room to land.
        pr = rng.randint(1, h - 2); pc = rng.randint(1, w - 2)
        g[pr][pc] = 9
        n = rng.randint(*nr)
        used = {(pr, pc)}
        placed = 0
        any_orbit = False
        for _ in range(n * 6):
            if placed >= n:
                break
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if (r, c) in used:
                continue
            used.add((r, c))
            g[r][c] = rng.randint(1, 8)
            placed += 1
            if _orbit_in_bounds(pr, pc, r, c, h, w):
                any_orbit = True
        # need at least one cell whose rotation lands in-bounds (output != input).
        if placed >= 1 and any_orbit:
            return g

    # deterministic fallback: pivot center + one cell with a full in-bounds orbit
    g = full_grid(7, 7, 0)
    g[3][3] = 9; g[1][3] = 2
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_pivot":
        # colored cells but no 9 -> rule has no pivot
        g[1][1] = 2; g[4][5] = 3
        return g
    if name == "pivot_only":
        # only the pivot -> output is just the pivot
        g[3][3] = 9
        return g
    if name == "cells_no_pivot":
        g[2][2] = 4; g[5][1] = 6
        return g
    return g
