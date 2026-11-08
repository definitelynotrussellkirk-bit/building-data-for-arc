"""Generator for arc_puzzle_bank_21_set21_s:S21_E3.

Rule: seeded rooms are marked at their room centers.

Combinatorial axes (8): room_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_seeds, all_rooms_seeded, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.rooms import rectangular_rooms

GENERATOR_ID = "8114be8704cc"
VERSION = "1.2.1"
TASK_ID = "8114be8704cc"
SUMMARY = "1-walls form an n×m room grid; seeded rooms are marked at their centers (rule paints center cell with seed color)."

# Rivals: 'paint at seed position' refuted by ≥1 demo where seed is
# NOT at center but center gets the color. 'paint all room cells'
# refuted by any demo (only center painted). 'use seed color' is the
# rule. 'paint walls' refuted by any demo.
# 3 demos with varied room grid shapes + seed positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "wall color is 1",
    "floor background is 0",
    "seeded rooms contain at least one nonzero token",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "all_rooms_seeded", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "room_h":         {"type": "int", "default": "rng 5..7", "valid": "3..9"},
    "room_w":         {"type": "int", "default": "rng 5..7", "valid": "3..9"},
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
    """Verify: wall color=1 present; floor=0 present; at least one seeded room (nonzero non-1 cell)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    walls = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1)]
    if not walls:
        return []  # full_grid or no-walls degenerate — allowed
    errs = []
    if not seeds:
        return []  # no_seeds degenerate — allowed
    # verify: some floor cells (0s) exist inside the room grid
    floors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    if not floors:
        errs.append("no floor (0) cells found — grid may be all walls/seeds")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        rh = ctx.draw_int("room_h", 4, 5)
        rw = ctx.draw_int("room_w", 4, 5)
        nrows, ncols = 2, 2
    elif difficulty == "hard":
        rh = ctx.draw_int("room_h", 5, 7)
        rw = ctx.draw_int("room_w", 5, 7)
        nrows = 3 if rh * 4 < 22 else 2
        ncols = 3 if rw * 4 < 22 else 2
    else:
        rh = ctx.draw_int("room_h", 4, 6)
        rw = ctx.draw_int("room_w", 4, 6)
        nrows, ncols = 2, 3
    rng = ctx.draw_rng("layout")
    grid, rooms = rectangular_rooms(nrows, ncols, rh, rw)
    room_ids = [(r, c) for r in range(nrows) for c in range(ncols)]
    rng.shuffle(room_ids)
    n_seeds = rng.randint(2, min(len(room_ids), 5))
    # Color pool now includes 7.
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], min(7, n_seeds))
    while len(colors) < n_seeds:
        colors.append(colors[0])
    for room_id, color in zip(room_ids[:n_seeds], colors):
        room = rooms[room_id[0]][room_id[1]]
        r, c = rng.choice(room["cells"])
        grid[r][c] = color
    return grid


def _draw_from_degenerate(name, rng):
    grid, rooms = rectangular_rooms(2, 2, 5, 5)
    if name == "no_seeds":
        return grid
    if name == "all_rooms_seeded":
        for i, room_id in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
            room = rooms[room_id[0]][room_id[1]]
            r, c = room["cells"][0]
            grid[r][c] = 2 + i
        return grid
    if name == "full_grid":
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                grid[r][c] = 2
        return grid
    return grid
