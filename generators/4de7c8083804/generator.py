"""Generator for arc_puzzle_bank_21_set22_s:S22_E1.

Rule: a target marker frame determines the local diagonal cell to mark.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frame, full_grid, blank.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.local_frame import choose_frame, draw_marker_frame

GENERATOR_ID = "4de7c8083804"
VERSION = "1.2.0"  # 1.2.0: add target-frame/local-diagonal self-check.
TASK_ID = "4de7c8083804"
SUMMARY = "Target marker frame determines the local diagonal cell to mark."

INVARIANTS = [
    "background is 0",
    "there is exactly one target frame with colors 5,6,7",
    "local coordinate (1,1) is in bounds and blank",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "full_grid", "blank")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "7..10"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "7..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_frame|full_grid|blank"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
    grid = full_grid(h, w, 0)
    origin, vx, vy = choose_frame(rng, h, w, [(1, 1)])
    draw_marker_frame(grid, origin, vx, vy, (5, 6, 7))
    return grid


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "no_frame":
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 5
        return g
    if name == "blank":
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h = len(grid); w = len(grid[0]) if h else 0
    frames = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5:
                continue
            for vx, vy in [((0, 1), (1, 0)), ((0, -1), (1, 0)), ((0, 1), (-1, 0)), ((0, -1), (-1, 0)),
                           ((1, 0), (0, 1)), ((-1, 0), (0, 1)), ((1, 0), (0, -1)), ((-1, 0), (0, -1))]:
                br, bc = r + vx[0], c + vx[1]
                cr, cc = r + vy[0], c + vy[1]
                dr, dc = r + vx[0] + vy[0], c + vx[1] + vy[1]
                if 0 <= br < h and 0 <= bc < w and 0 <= cr < h and 0 <= cc < w and 0 <= dr < h and 0 <= dc < w:
                    if grid[br][bc] == 6 and grid[cr][cc] == 7:
                        frames.append((r, c, dr, dc))
    if len(frames) != 1:
        msgs.append(f"expected exactly one 5/6/7 marker frame, got {len(frames)}")
    elif grid[frames[0][2]][frames[0][3]] != 0:
        msgs.append("local diagonal target cell must start blank")
    for color in (5, 6, 7):
        if sum(v == color for row in grid for v in row) != 1:
            msgs.append(f"expected one marker color {color}")
    return msgs
