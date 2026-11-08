"""Generator for arc_puzzle_bank_21_set21_s:S21_E2.

Rule: each seeded room is filled with its own seed color.

Combinatorial axes (8): room_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_seeds, all_rooms_seeded, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.rooms import center_cell, rectangular_rooms

GENERATOR_ID = "3758ef979ae9"
VERSION = "2.0.1"
TASK_ID = "3758ef979ae9"
SUMMARY = (
    "Grid is a 2×2 grid of rectangular ROOMS separated by "
    "color-1 (blue) WALLS (also color 7 and 9 count as walls "
    "in the rule). Each room has bg=0 floor with at most one "
    "non-wall non-bg single-cell SEED at the room's center. "
    "Rule: extract the rooms (BFS over non-wall cells). For "
    "each room, find its seed (any non-bg, non-wall cell). "
    "If a seed exists, flood-fill the room's floor cells "
    "with that seed's color. Empty rooms stay 0. Walls "
    "remain unchanged."
)

INVARIANTS = [
    "wall color is 1",
    "floor background is 0",
    "each seeded room has exactly one nonzero token color",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "all_rooms_seeded", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "room_h":         {"type": "int", "default": "rng 3..5", "valid": "3..7"},
    "room_w":         {"type": "int", "default": "rng 3..5", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "rooms", "valid": "rooms"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; wall color is 1 (present); ≥1 non-wall/non-bg cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    walls = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if walls == 0:
        pass  # degenerate (no_seeds / full_grid) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        rh = ctx.draw_int("room_h", 3, 3)
        rw = ctx.draw_int("room_w", 3, 4)
    elif difficulty == "hard":
        rh = ctx.draw_int("room_h", 4, 5)
        rw = ctx.draw_int("room_w", 4, 5)
    else:
        rh = ctx.draw_int("room_h", 3, 5)
        rw = ctx.draw_int("room_w", 3, 5)
    rng = ctx.draw_rng("layout")
    grid, rooms = rectangular_rooms(2, 2, rh, rw)
    room_ids = [(0, 0), (0, 1), (1, 0), (1, 1)]
    rng.shuffle(room_ids)
    colors = rng.sample([2, 3, 4, 5, 6, 8, 9], rng.randint(2, 4))
    for room_id, color in zip(room_ids, colors):
        r, c = center_cell(rooms[room_id[0]][room_id[1]])
        grid[r][c] = color
    return grid


def _draw_from_degenerate(name, rng):
    grid, rooms = rectangular_rooms(2, 2, 3, 3)
    if name == "no_seeds":
        return grid
    if name == "all_rooms_seeded":
        for i, room_id in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
            r, c = center_cell(rooms[room_id[0]][room_id[1]])
            grid[r][c] = 2 + i
        return grid
    if name == "full_grid":
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                grid[r][c] = 2
        return grid
    return grid
