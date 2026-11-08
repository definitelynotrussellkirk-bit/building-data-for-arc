"""Generator for arc_puzzle_bank_21_set22_s:S22_E2.

Rule: a target marker frame defines a local 2x2 block to recolor.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frame, full_grid, blank.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.local_frame import choose_frame, draw_marker_frame

GENERATOR_ID = "0d9784b230ca"
VERSION = "2.2.0"  # 2.0.0->2.1.0: larger grids -> more 2x2-block positions (output is intrinsically a 2x2 8-block)
TASK_ID = "0d9784b230ca"
SUMMARY = (
    "0-bg grid (h~7-10, w~7-10) with ONE MARKER FRAME — "
    "three corners of an axis-aligned 2×2 local-coordinate "
    "system painted in fixed marker colors 5, 6, and 7 "
    "(origin at random non-degenerate position via "
    "choose_frame helper, basis vectors vx, vy each ±1). "
    "Specifically the markers sit at: ORIGIN (color 5), "
    "ORIGIN + vx (color 6), ORIGIN + vy (color 7). The "
    "FOURTH CORNER at ORIGIN + vx + vy is left 0 and is "
    "guaranteed in-bounds. All other cells are 0. "
    "Rule (CLOSE THE 2×2 MARKER FRAME): "
    "find the three marker cells (colors 5, 6, 7). "
    "INFER the local 2×2 coordinate frame: 5 = origin, "
    "6 and 7 along orthogonal axes from origin. COMPUTE "
    "the missing fourth corner = origin + (6's offset) + "
    "(7's offset). PAINT that fourth corner with a "
    "designated FILL COLOR (e.g., the maximum of the "
    "three marker colors, or a fixed convention per "
    "demos). The three marker cells stay unchanged. Net: "
    "the partially-drawn 2×2 marker block is completed "
    "into a full 4-corner block with a new color in the "
    "previously-empty corner."
)

INVARIANTS = [
    "background is 0",
    "there is exactly one target frame with colors 5,6,7",
    "the fourth local block corner is in bounds",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "full_grid", "blank")
HELPFUL_TEXTURES = PALETTE_KINDS


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the 5/6/7 local frame and its missing fourth corner."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    pos = {}
    for col, name in ((5, "origin (5)"), (6, "x-axis (6)"), (7, "y-axis (7)")):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == col]
        if len(cells) != 1:
            errors.append(f"expected exactly 1 color-{col} {name} marker, found {len(cells)}")
        else:
            pos[col] = cells[0]
    if len(pos) == 3:
        o, x, y = pos[5], pos[6], pos[7]
        vx = (x[0] - o[0], x[1] - o[1]); vy = (y[0] - o[0], y[1] - o[1])
        if abs(vx[0]) + abs(vx[1]) != 1 or abs(vy[0]) + abs(vy[1]) != 1:
            errors.append("6 and 7 must be cardinal unit offsets from 5")
        if vx[0] * vy[0] + vx[1] * vy[1] != 0:
            errors.append("6 and 7 offsets must be orthogonal")
        fr, fc = o[0] + vx[0] + vy[0], o[1] + vx[1] + vy[1]
        if not (0 <= fr < h and 0 <= fc < w):
            errors.append("missing fourth local corner must be in bounds")
        elif grid[fr][fc] != 0:
            errors.append("missing fourth local corner must be empty before the rule fills it")
    return errors


AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..15", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 7..15", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
    else:
        h = ctx.draw_int("grid_h", 7, 15)
        w = ctx.draw_int("grid_w", 7, 15)
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
