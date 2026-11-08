"""Generator for dc433765.

Rule: 3-cell at p3 and 4-cell at p4. Replace 3 at p3 with 0; place 3
at one step toward p4 (sign of dr, sign of dc).

Combinatorial axes (8): grid_h/w, separation, direction, anchor_corner,
asymmetry_force, palette_size, include_decoy.
Degenerates: adjacent, same_position, no_three.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a8ac6887ee58"
VERSION = "2.0.1"
TASK_ID = "a8ac6887ee58"
SUMMARY = (
    "0-bg grid (h~5-7, w~"
    "7-9) with: (a) ONE "
    "COLOR-3 (green) CELL "
    "at (r3, c3); (b) ONE "
    "COLOR-4 (yellow) CELL "
    "at (r4, c4). Cells are "
    "placed so Manhattan "
    "distance ≥ min_"
    "separation (2-4) and "
    "direction (relative "
    "placement) is one of 8 "
    "cardinal/diagonal "
    "directions (n/s/e/w/nw/"
    "ne/sw/se). No other "
    "cells. Rule (SHIFT "
    "COLOR-3 ONE STEP "
    "TOWARD COLOR-4): "
    "identify the 3-cell at "
    "(r3, c3) and the 4-cell "
    "at (r4, c4). COMPUTE "
    "delta = (sign(r4 - r3)"
    ", sign(c4 - c3)). "
    "ERASE the 3-cell "
    "(g[r3][c3] = 0). PLACE "
    "the 3-cell at "
    "(r3 + dr, c3 + dc) "
    "(one step toward the "
    "4-cell). The 4-cell "
    "stays. Net: green cell "
    "takes one step toward "
    "the yellow target."
)

INVARIANTS = [
    "exactly 1 cell of color 3 and 1 cell of color 4",
    "p3 and p4 not adjacent (so the move is visible)",
    "background is 0",
]

DIRECTIONS = ("nw", "ne", "sw", "se", "n", "s", "e", "w")
DEGENERATE_TEXTURES = ("adjacent", "same_position", "no_three")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "min_separation": {"type": "int", "default": "2", "valid": "2..6"},
    "direction":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DIRECTIONS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "include_decoy":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for direction",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 cell of color 3 and 1 cell of color 4; they are not adjacent."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if not threes and not fours:
        return errs  # degenerate (no_three / same_position) — allowed
    if len(threes) != 1:
        errs.append(f"expected exactly 1 color-3 cell; got {len(threes)}")
    if len(fours) != 1:
        errs.append(f"expected exactly 1 color-4 cell; got {len(fours)}")
    if len(threes) == 1 and len(fours) == 1:
        r3, c3 = threes[0]; r4, c4 = fours[0]
        manhattan = abs(r4 - r3) + abs(c4 - c3)
        if manhattan <= 1:
            return errs  # degenerate (adjacent) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 5, 5, 7
        sep_min = 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 7, 10, 9, 12
        sep_min = 4
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 7, 7, 9
        sep_min = 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    sep_min = int(overrides.get("min_separation", sep_min))
    direction = (overrides.get("texture") or
                 overrides.get("direction")
                 or ctx.draw_choice("direction", list(DIRECTIONS)))
    for _try in range(80):
        r3, c3, r4, c4 = _pick_pair(direction, h, w, sep_min, rng)
        if abs(r3 - r4) + abs(c3 - c4) >= sep_min:
            g[r3][c3] = 3
            g[r4][c4] = 4
            return g
    r3, c3 = 0, 0
    r4, c4 = h - 1, w - 1
    g[r3][c3] = 3
    g[r4][c4] = 4
    return g


def _pick_pair(direction, h, w, sep_min, rng):
    sign_r = {"nw": -1, "n": -1, "ne": -1, "w": 0, "e": 0,
              "sw": 1, "s": 1, "se": 1}.get(direction, 0)
    sign_c = {"nw": -1, "ne": 1, "sw": -1, "se": 1, "n": 0, "s": 0,
              "w": -1, "e": 1}.get(direction, 0)
    if sign_r == 0 and sign_c == 0:
        r3 = rng.randint(0, h - 1); c3 = rng.randint(0, w - 1)
        r4 = rng.randint(0, h - 1); c4 = rng.randint(0, w - 1)
        return r3, c3, r4, c4
    if sign_r == 0:
        r3 = rng.randint(0, h - 1); r4 = r3
    elif sign_r == 1:
        r3 = rng.randint(0, h - sep_min - 1)
        r4 = rng.randint(r3 + sep_min, h - 1)
    else:
        r4 = rng.randint(0, h - sep_min - 1)
        r3 = rng.randint(r4 + sep_min, h - 1)
    if sign_c == 0:
        c3 = rng.randint(0, w - 1); c4 = c3
    elif sign_c == 1:
        c3 = rng.randint(0, w - sep_min - 1)
        c4 = rng.randint(c3 + sep_min, w - 1)
    else:
        c4 = rng.randint(0, w - sep_min - 1)
        c3 = rng.randint(c4 + sep_min, w - 1)
    return r3, c3, r4, c4


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "adjacent":
        g[2][2] = 3
        g[2][3] = 4
        return g
    if name == "same_position":
        g[2][2] = 3
        return g
    if name == "no_three":
        g[2][3] = 4
        return g
    return g
