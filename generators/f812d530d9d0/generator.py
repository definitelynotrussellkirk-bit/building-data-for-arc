"""Generator for arc_puzzle_bank_21_set24_bundle:easy_p03.

Rule: each isolated solid monochrome 2x2 square expands into the surrounding 4x4
RING (the border cells around it), drawn in the square's color; the 2x2 stays.

Combinatorial axes: grid size, number of squares, colors, positions, and non-2x2
DISTRACTOR objects the rule leaves untouched.
Degenerates: no_squares, single_cell, on_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f812d530d9d0"
VERSION = "2.0.1"  # FIX: require the requested number of ringable 2x2 squares; easy could silently underfill.
TASK_ID = "f812d530d9d0"
SUMMARY = (
    "0-bg grid (size varies) with several solid monochrome 2x2 SQUARES at "
    "isolated interior positions in distinct colors, plus NON-2x2 DISTRACTOR "
    "objects (single cells, dominoes, L/I/T shapes — no solid 2x2). Rule: for "
    "each solid 2x2 block, draw the surrounding 4x4 RING (its border ring of "
    "cells) in the block's color; the 2x2 itself stays. Non-2x2 objects are "
    "left untouched. Net: each square blooms into a 4x4 outline. (Was small "
    "grids, no distractors.)"
)

INVARIANTS = [
    "background is 0",
    ">=1 solid monochrome 2x2 square with a 1-cell margin for its ring",
    "distractor objects contain no solid 2x2 (rule leaves them unchanged)",
    "the rule expands exactly the intended 2x2 squares (verified by mirror)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_squares", "single_cell", "on_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-11 easy / 11-15 med / 14-20 hard", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "9-13 easy / 13-17 med / 16-22 hard", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_squares":      {"type": "int", "default": "2-3 easy / 3-5 med / 4-7 hard", "valid": "1..7"},
    "n_decoys":       {"type": "int", "default": "0-1 easy / 1-2 med / 2-3 hard", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "per-object colors", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_2x2_squares",
                       "valid": "isolated_2x2_squares"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_DISTRACTORS = [
    [(0, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (1, 0), (1, 1)],                 # L-tromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],         # T
]


def _fires(g):
    """TL corners of every solid same-color non-zero 2x2 (what the rule expands)."""
    h, w = len(g), len(g[0])
    out = set()
    for r in range(h - 1):
        for c in range(w - 1):
            v = g[r][c]
            if v != 0 and g[r][c + 1] == v and g[r + 1][c] == v and g[r + 1][c + 1] == v:
                out.add((r, c))
    return out


def _free(occ, cells, r0, c0, h, w):
    for dr, dc in cells:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < h and 0 <= c < w):
            return False
        for hr in range(r - 1, r + 2):
            for hc in range(c - 1, c + 2):
                if 0 <= hr < h and 0 <= hc < w and occ[hr][hc]:
                    return False
    return True


def _place(g, occ, cells, color, rng, margin=1):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
    for _ in range(80):
        r0 = rng.randint(margin, h - sh - margin); c0 = rng.randint(margin, w - sw - margin)
        if r0 < 0 or c0 < 0:
            return None
        if _free(occ, cells, r0, c0, h, w):
            for dr, dc in cells:
                g[r0 + dr][c0 + dc] = color
                occ[r0 + dr][c0 + dc] = True
            # also reserve the 1-ring around so rings don't collide
            for dr, dc in cells:
                for hr in range(r0 + dr - 1, r0 + dr + 2):
                    for hc in range(c0 + dc - 1, c0 + dc + 2):
                        if 0 <= hr < h and 0 <= hc < w:
                            occ[hr][hc] = True
            return (r0, c0)
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, sr, dr_ = (8, 11), (9, 13), (2, 3), (0, 1)
    elif difficulty == "hard":
        hr, wr, sr, dr_ = (14, 20), (16, 22), (4, 7), (2, 3)
    else:
        hr, wr, sr, dr_ = (11, 15), (13, 17), (3, 5), (1, 2)
    rng = ctx.draw_rng("layout")
    square = [(0, 0), (0, 1), (1, 0), (1, 1)]

    for _attempt in range(30):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        cols = [1, 2, 3, 4, 5, 6, 7, 8, 9]; rng.shuffle(cols)
        intended = set()
        desired = rng.randint(*sr)
        for i in range(desired):
            pos = _place(g, occ, square, cols[i % len(cols)], rng, margin=1)
            if pos:
                intended.add(pos)
        if len(intended) != desired:
            continue
        for j in range(rng.randint(*dr_)):
            _place(g, occ, rng.choice(_DISTRACTORS), cols[(len(intended) + j) % len(cols)], rng, margin=0)
        if _fires(g) == intended:        # rule expands exactly the intended 2x2 squares
            return g

    g = full_grid(8, 9, 0)
    g[3][3] = g[3][4] = g[4][3] = g[4][4] = 4
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Default episodes must contain the requested quota of ringable 2x2 triggers."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    fires = _fires(grid)
    min_squares = 4 if difficulty == "hard" else (2 if difficulty == "easy" else 3)
    errors: list[str] = []
    if len(fires) < min_squares:
        errors.append(f"expected at least {min_squares} solid 2x2 squares, got {len(fires)}")
    for r, c in fires:
        if r < 1 or c < 1 or r + 2 >= h or c + 2 >= w:
            errors.append("a 2x2 square lacks a one-cell margin for its 4x4 ring")
            break
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_squares":
        return g
    if name == "single_cell":
        g[3][3] = 4; g[6][6] = 6
        return g
    if name == "on_edge":
        for r in range(2):
            for c in range(2):
                g[r][c] = 4
        return g
    return g
