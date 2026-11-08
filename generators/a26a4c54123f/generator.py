"""Generator for arc_puzzle_bank_21_set21_s:S21_E7.

Rule: rooms are the connected non-wall regions (walls are colors 1/7/9);
color-7 cells are DOORS connecting the two rooms they sit between. Find
the room containing the red(2) SEED, follow its door to the adjacent
room, and output a grid of just the walls+doors with that adjacent
(target) room filled COLOR 8. (The seed and all other rooms are dropped
to 0 — the output keeps only the walls and the one filled room.)

Combinatorial axes: the room-grid layout (R x C), room size, which room
is seeded, which door direction the seed points through, and the
distractor doors elsewhere.
Degenerates: no_seed, no_door, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.rooms import (add_door_between,
                                             center_cell,
                                             rectangular_rooms)

GENERATOR_ID = "a26a4c54123f"
VERSION = "3.0.2"  # fix no_door degenerate + executable seed-door invariant
TASK_ID = "a26a4c54123f"
SUMMARY = (
    "A grid of rooms (R x C, total >=2) built by rectangular_rooms with "
    "COLOR-1 (blue) walls and uniform room interiors (size 3..6). The "
    "SEEDED room holds one COLOR-2 (red) cell at a random interior cell "
    "and has "
    "EXACTLY ONE COLOR-7 (orange) DOOR to a neighbour (the target). 0-2 "
    "extra distractor doors connect OTHER room pairs (never the seed "
    "room). Rule (DOOR-DIRECTED FILL): find the seeded room, follow its "
    "single door to the adjacent room, and output walls+doors with that "
    "target room filled COLOR 8 (everything else 0). The layout, room "
    "size, seeded room, door direction and distractor doors all vary "
    "freely (was a fixed 1x2 layout x 3 sizes)."
)

INVARIANTS = [
    "walls are color 1, doors are color 7",
    "the red(2)-seeded room has exactly one door (one neighbour = the target)",
    "distractor doors never touch the seeded room",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seed", "no_door", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "str", "default": "varied", "valid": "varied"},
    "grid_w":         {"type": "str", "default": "varied", "valid": "varied"},
    "room_h":         {"type": "int", "default": "varies", "valid": "3..6"},
    "room_w":         {"type": "int", "default": "varies", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_seed|no_door|full_grid"},
}

_LAYOUTS_EASY = [(1, 2), (2, 1), (1, 3), (3, 1)]
_LAYOUTS_DEF = [(1, 2), (2, 1), (1, 3), (3, 1), (2, 2), (2, 3), (3, 2)]
_LAYOUTS_HARD = [(2, 2), (2, 3), (3, 2), (3, 3), (1, 4), (4, 1)]


def _neighbors(coord, R, C):
    r, c = coord
    out = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < R and 0 <= nc < C:
            out.append((nr, nc))
    return out


def _room_components(grid):
    """Room interiors; walls(1) and doors(7) remain barriers."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] in (1, 7):
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] not in (1, 7):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Seeded room must have exactly one adjacent door; distractor doors avoid it."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        errs.append("no color-1 wall cells found")
    if len(twos) != 1:
        errs.append(f"expected exactly 1 color-2 seed, found {len(twos)}")
    if not sevens:
        errs.append("no color-7 door cells found")
    if len(twos) == 1:
        seed = twos[0]
        comps = _room_components(grid)
        seed_comp = None
        for cells in comps:
            if seed in cells:
                seed_comp = set(cells)
                break
        if not seed_comp:
            errs.append("seed is not inside a room component")
        else:
            adjacent_doors = set()
            for r, c in seed_comp:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 7:
                        adjacent_doors.add((nr, nc))
            if len(adjacent_doors) != 1:
                errs.append(f"seeded room should touch exactly one door, found {len(adjacent_doors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        layouts, szr, ndr = _LAYOUTS_EASY, (3, 5), (0, 0)
    elif difficulty == "hard":
        layouts, szr, ndr = _LAYOUTS_HARD, (3, 7), (1, 3)
    else:
        layouts, szr, ndr = _LAYOUTS_DEF, (3, 6), (0, 2)

    R, C = rng.choice(layouts)
    rh = rng.randint(*szr); rw = rng.randint(*szr)
    grid, rooms = rectangular_rooms(R, C, rh, rw)

    coords = [(rr, cc) for rr in range(R) for cc in range(C)]
    # all unordered cardinal-adjacent room pairs
    pairs = []
    for a in coords:
        for b in _neighbors(a, R, C):
            if a < b:
                pairs.append((a, b))

    seed_room = rng.choice(coords)
    target = rng.choice(_neighbors(seed_room, R, C))
    add_door_between(grid, rooms, seed_room, target)

    # distractor doors: among pairs NOT touching the seed room (and not the seed→target door)
    used = (min(seed_room, target), max(seed_room, target))
    cand = [p for p in pairs if seed_room not in p and p != used]
    n_extra = rng.randint(*ndr)
    for p in rng.sample(cand, min(n_extra, len(cand))):
        add_door_between(grid, rooms, p[0], p[1])

    # the rule finds the seed room by ANY color-2 cell, so the seed may sit
    # at any interior cell — its position varies the input without changing
    # the (room-level) output.
    r, c = rng.choice(rooms[seed_room[0]][seed_room[1]]["cells"])
    grid[r][c] = 2
    return grid


def _draw_from_degenerate(name, rng):
    grid, rooms = rectangular_rooms(1, 2, 3, 3)
    if name == "no_seed":
        add_door_between(grid, rooms, (0, 0), (0, 1))
        return grid
    if name == "no_door":
        r, c = center_cell(rooms[0][0])
        grid[r][c] = 2
        return grid
    if name == "full_grid":
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                grid[r][c] = 1
        return grid
    return grid
