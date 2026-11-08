"""Generator for arc_additional_puzzles_21_set6:M39 — Gravity by command.

Rule: at (0,0) is a command. work = grid with (0,0) zeroed:
  - cmd 1: gravity work "down"
  - cmd 2: gravity work "up"
  - cmd 3: gravity work "left"
  - else: gravity work "right"

Combinatorial axes (8): grid_h, grid_w, palette_kind, cmd, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_payload, payload_already_settled, full_payload.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3bf9215de862"
VERSION = "1.1.1"
TASK_ID = "3bf9215de862"
SUMMARY = "Sparse non-zero cells + command at (0,0) selecting gravity direction."

INVARIANTS = [
    "(0,0) holds cmd in {1, 2, 3, 4}",
    "between 4 and 10 scattered non-zero cells",
    "scattered cells leave the perpendicular direction with bg below/above/left/right of at least one cell so gravity moves something",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_payload", "payload_already_settled", "full_payload")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cmd":            {"type": "int", "default": "rng 1..4", "valid": "1..9"},
    "n_cells":        {"type": "int", "default": "rng 4..10", "valid": "2..20"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "command_corner",
                       "valid": "command_corner"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: cell(0,0) is a gravity command in {1,2,3,4}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    cmd = grid[0][0]
    if cmd not in (1, 2, 3, 4):
        errs.append(f"cell(0,0)={cmd} is not a valid gravity command (expected 1-4)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
        cmd = ctx.draw_int("cmd", 1, 4)
        n_cells = ctx.draw_int("n_cells", 4, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        cmd = ctx.draw_int("cmd", 1, 4)
        n_cells = ctx.draw_int("n_cells", 8, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
        cmd = ctx.draw_int("cmd", 1, 4)
        n_cells = ctx.draw_int("n_cells", 4, 10)

    g = full_grid(h, w, 0)
    g[0][0] = cmd
    rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    positions = [(r, c) for r in range(h) for c in range(w) if (r, c) != (0, 0)]
    rng.shuffle(positions)
    for r, c in positions[:n_cells]:
        g[r][c] = color_rng.randint(1, 9)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    g[0][0] = 1  # cmd=down
    if name == "empty_payload":
        # cmd present but no scattered cells → gravity has nothing to move
        return g
    if name == "payload_already_settled":
        # cmd=down, but all payload is already on the bottom row → gravity is identity
        g[h - 1][1] = 4; g[h - 1][3] = 5; g[h - 1][5] = 6
        return g
    if name == "full_payload":
        # every interior cell filled → no bg to fall into, gravity is identity
        for r in range(h):
            for c in range(w):
                if (r, c) == (0, 0): continue
                g[r][c] = 4 if (r + c) % 2 == 0 else 6
        return g
    return g
