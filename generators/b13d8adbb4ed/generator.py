"""Generator for 12b:m79 — rotate cropped object by control color.

Rule: cell (0,0) is a control code; the body has a single asymmetric
shape. Output is the body cropped and transformed per code.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_control, no_shape, symmetric_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b13d8adbb4ed"
VERSION = "2.0.0"
TASK_ID = "b13d8adbb4ed"
SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) with: "
    "(a) cell (0, 0) holds a CONTROL "
    "CODE in {1, 2, 3, 4, 5}; (b) "
    "EXACTLY ONE isolated ASYMMETRIC "
    "SHAPE (3-6 cells from a bank of "
    "9 asymmetric tetro/pent shapes) "
    "in some non-control color "
    "elsewhere in the grid (rows 2+, "
    "cols 2+) with 1-cell padding. "
    "Rule (CONTROL-CODE TRANSFORM "
    "CROP): CLEAR cell (0, 0). CROP "
    "the remaining grid to its "
    "non-zero CONTENT BBOX (the "
    "shape's bbox). APPLY the "
    "TRANSFORM indexed by the "
    "control code: 1 = identity, "
    "2 = rotate CW 90°, 3 = "
    "rotate 180°, 4 = rotate CCW "
    "90°, 5 = flip horizontal. "
    "OUTPUT: the cropped, "
    "transformed shape. Net: code "
    "cell at (0, 0) picks the "
    "geometric transform applied "
    "to the cropped asymmetric "
    "shape."
)

# Rivals: 'output is input' refuted by demos (output is small).
# 'always identity (code 1)' refuted by demos with codes 2..6.
# 'use control color in output' refuted by demos preserving shape
# color. 'crop without transform' refuted by demos with asymmetric
# shapes showing transform applied. 'transform without crop' refuted
# by demos showing tight bbox. 4 demos covering codes 1..5 pin the
# transform table.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "cell (0, 0) is a control code in {1..6} (NOT 0)",
    "exactly one isolated asymmetric shape (3-6 connected cells) elsewhere",
    "shape color ≠ control code (so the rule's clear-then-crop is unambiguous)",
    "shape is asymmetric (not rotation- or reflection-invariant)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_control", "no_shape", "symmetric_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "control_corner_shape_inside",
                       "valid": "control_corner_shape_inside"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_ASYM_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],                   # L-tetromino
    [(0, 0), (0, 1), (1, 0)],                           # L-tromino
    [(0, 0), (1, 0), (1, 1), (2, 1)],                   # S-tetromino
    [(0, 0), (0, 1), (0, 2), (1, 0)],                   # J-tetromino
    [(0, 0), (1, 0), (1, 1), (1, 2)],                   # T-rotated
    [(0, 0), (0, 1), (1, 1), (2, 1)],                   # J flipped
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],           # zigzag-5
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],           # T-down-tall
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],           # L-5 tall
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    code = rng.randint(1, 5)
    g[0][0] = code
    color = rng.choice([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != code])
    shape = rng.choice(_ASYM_SHAPES)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(2, h - sh); c0 = rng.randint(2, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_control":
        # Shape but (0,0) empty — rule's transform code lookup fails.
        for r, c in [(3, 3), (4, 3), (5, 3), (5, 4)]: g[r][c] = 4
        return g
    if name == "no_shape":
        # Control code but no body shape — rule has nothing to crop.
        g[0][0] = 2
        return g
    if name == "symmetric_shape":
        # Shape is rotation/flip-symmetric — every transform produces
        # the same shape; rule's effect is invisible regardless of
        # control code.
        g[0][0] = 2
        for r, c in [(3, 3), (3, 4), (4, 3), (4, 4)]: g[r][c] = 4
        return g
    return g

def _sc_components(grid):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0: continue
            col = grid[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == col:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((col, cells))
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    code = grid[0][0]
    if code not in (1, 2, 3, 4, 5): errs.append(f"bad transform code {code}")
    body = [row[:] for row in grid]; body[0][0] = 0
    comps = _sc_components(body)
    if len(comps) != 1: return errs + [f"expected one body component, got {len(comps)}"]
    color, cells = comps[0]
    if color == code: errs.append("shape color equals control code")
    if not (3 <= len(cells) <= 6): errs.append(f"shape size should be 3..6, got {len(cells)}")
    return errs
