"""Generator for arc_puzzle_bank_21_set21_s:S21_E6.

Rule: a strip flags rooms that contain yellow tokens.

Combinatorial axes (8): grid_h/w, room_h, room_w, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_tokens, all_rooms, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.rooms import center_cell, rectangular_rooms

GENERATOR_ID = "a1be3b493725"
VERSION = "2.1.1"  # avoid all-rooms-flagged samples: v2.0 allowed k=n_rooms, so ~10-30% of generated outputs collapsed to an all-8 strip. Keep at least one positive and one negative room so every demo teaches the discriminator.
TASK_ID = "a1be3b493725"
SUMMARY = "A 1xN strip (N = number of rooms, in top-left scan order) flags with color-8 each rectangular room that contains a color-4 token. Room-grid layout (R x C), room size, and which rooms are flagged all vary."

INVARIANTS = [
    "wall color is 1",
    "floor background is 0",
    "room order is top-left to bottom-right",
    "some, but not all, rooms contain color 4",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_tokens", "all_rooms", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varied", "valid": "varied"},
    "grid_w":         {"type": "int", "default": "varied", "valid": "varied"},
    "room_h":         {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "room_w":         {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """color-1 walls partitioning rooms; >=1 color-4 token; >=1 zero-floor cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    zeros = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    if not ones:
        errs.append("no color-1 wall cells found")
    if not fours:
        errs.append("no color-4 token cells found")
    if not zeros:
        errs.append("no zero floor cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # Output strip length = room count, so vary the room grid R x C (the rule
    # works for any layout: it lists rooms top-left first and flags those with a
    # color-4 token). v1.x hardcoded 2x3 -> output always 1x6.
    if difficulty == "easy":
        layouts = [(1, 3), (3, 1), (2, 2), (1, 4)]
        rh = ctx.draw_int("room_h", 3, 3)
        rw = ctx.draw_int("room_w", 3, 3)
    elif difficulty == "hard":
        layouts = [(2, 4), (4, 2), (3, 3), (2, 5), (3, 4)]
        rh = ctx.draw_int("room_h", 4, 5)
        rw = ctx.draw_int("room_w", 4, 5)
    else:
        layouts = [(2, 3), (3, 2), (2, 4), (1, 5), (2, 2), (1, 4)]
        rh = ctx.draw_int("room_h", 3, 5)
        rw = ctx.draw_int("room_w", 3, 5)
    R, C = rng.choice(layouts)
    grid, rooms = rectangular_rooms(R, C, rh, rw)
    room_ids = [(r, c) for r in range(R) for c in range(C)]
    n_rooms = len(room_ids)
    # Need both positive and negative examples inside every strip. If all rooms
    # contain a token, the output is a constant all-8 row and the task no longer
    # demonstrates the room-level discriminator.
    k = rng.randint(1, n_rooms - 1)
    for room_id in rng.sample(room_ids, k):
        r, c = center_cell(rooms[room_id[0]][room_id[1]])
        grid[r][c] = 4
    return grid


def _draw_from_degenerate(name, rng):
    grid, rooms = rectangular_rooms(2, 3, 3, 3)
    if name == "no_tokens":
        return grid
    if name == "all_rooms":
        for ri in range(2):
            for ci in range(3):
                r, c = center_cell(rooms[ri][ci])
                grid[r][c] = 4
        return grid
    if name == "full_grid":
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                grid[r][c] = 1
        return grid
    return grid
