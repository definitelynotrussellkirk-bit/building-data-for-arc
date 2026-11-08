"""Generator for arc_puzzle_bank_21_set21_s:S21_H1 — adjacency matrix of the room graph.

Rule (verified from canonical Racket): wall cells are colours {1,7,9}; ROOMS are
the 4-connected regions of non-wall cells; colour-7 DOORS connect the rooms in
their cardinal neighbourhood. Build the room adjacency graph and output the n x n
adjacency matrix (rooms in reading order), 8 where two rooms share a door, else 0.

The previous body was the generic scatter template; with no walls the whole grid
is one room, so the matrix is 1x1 [[0]] every time (distinct_out=1). This rewrite
CONSTRUCTS a floor plan: an nr x nc grid of rooms separated by colour-1 walls,
with colour-7 doors punched between adjacent rooms — so the adjacency matrix
varies with the layout and door set.

Axes: room grid shape, room sizes, which doors exist.
Degenerates: single_room, no_doors, fully_connected.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "48c1d2b69c55"
VERSION = "2.1.0"  # out-shapes only 3 (nr,nc pinned to {2,3} -> N in {4,6,9}): widened room grid to nr,nc 2..4 (N up to 16, matrix N x N <= 30) for more matrix sizes + door-subset combos. distinct 104->123, out 3->5.
TASK_ID = "48c1d2b69c55"

SUMMARY = ("A floor plan of rooms separated by colour-1 walls, with colour-7 doors between "
           "some adjacent rooms; the rule outputs the n x n room adjacency matrix (8 where two "
           "rooms share a door). Room-grid shape, room sizes and the door set vary.")

INVARIANTS = [
    "rooms are 4-connected colour-0 regions enclosed by colour-1 walls",
    "colour-7 doors sit in the wall between two adjacent rooms",
    "the room count equals nr*nc; output is the nr*nc square adjacency matrix",
]

DEGENERATE_TEXTURES = ("single_room", "no_doors", "fully_connected")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "n_rows":     {"type": "int", "default": "rng 2..3 (room rows)", "valid": "1..4"},
    "n_cols":     {"type": "int", "default": "rng 2..3 (room cols)", "valid": "1..4"},
    "room_h":     {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "room_w":     {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "door_prob":  {"type": "float", "default": "0.6", "valid": "0..1"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|single_room|no_doors|fully_connected"},
}


def _floor_plan(nr, nc, rh, rw, doors_h, doors_v):
    """Build the grid. doors_h[(i,j)] -> door between room (i,j)&(i,j+1);
    doors_v[(i,j)] -> door between (i,j)&(i+1,j). Each maps to an interior offset."""
    h = 1 + nr * (rh + 1)
    w = 1 + nc * (rw + 1)
    g = full_grid(h, w, 1)                       # all walls (colour 1)

    def r0(i): return 1 + i * (rh + 1)
    def c0(j): return 1 + j * (rw + 1)

    for i in range(nr):
        for j in range(nc):
            for r in range(r0(i), r0(i) + rh):
                for c in range(c0(j), c0(j) + rw):
                    g[r][c] = 0                  # open room interior
    # vertical-wall doors (connect horizontally-adjacent rooms)
    for (i, j), off in doors_h.items():
        dc = c0(j) + rw                          # wall column between (i,j) and (i,j+1)
        dr = r0(i) + off
        g[dr][dc] = 7
    # horizontal-wall doors (connect vertically-adjacent rooms)
    for (i, j), off in doors_v.items():
        dr = r0(i) + rh                          # wall row between (i,j) and (i+1,j)
        dc = c0(j) + off
        g[dr][dc] = 7
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # room COUNT (nr*nc) = adjacency-matrix size N; widen it for more matrix
    # sizes AND more door-subset combinations (output N x N, N<=16 -> <=30).
    if difficulty == "easy":
        nr = ctx.draw_int("n_rows", 2, 2); nc = ctx.draw_int("n_cols", 2, 3)
        rh = ctx.draw_int("room_h", 2, 2); rw = ctx.draw_int("room_w", 2, 3)
    elif difficulty == "hard":
        nr = ctx.draw_int("n_rows", 3, 4); nc = ctx.draw_int("n_cols", 3, 4)
        rh = ctx.draw_int("room_h", 2, 3); rw = ctx.draw_int("room_w", 2, 3)
    else:
        nr = ctx.draw_int("n_rows", 2, 3); nc = ctx.draw_int("n_cols", 2, 4)
        rh = ctx.draw_int("room_h", 2, 3); rw = ctx.draw_int("room_w", 2, 3)
    rng = ctx.draw_rng("layout")

    doors_h, doors_v = {}, {}
    for i in range(nr):
        for j in range(nc):
            if j + 1 < nc and rng.random() < 0.6:
                doors_h[(i, j)] = rng.randint(0, rh - 1)
            if i + 1 < nr and rng.random() < 0.6:
                doors_v[(i, j)] = rng.randint(0, rw - 1)
    # guarantee at least one door so the matrix has an off-diagonal 8
    if not doors_h and not doors_v:
        if nc > 1:
            doors_h[(0, 0)] = rng.randint(0, rh - 1)
        elif nr > 1:
            doors_v[(0, 0)] = rng.randint(0, rw - 1)
    return _floor_plan(nr, nc, rh, rw, doors_h, doors_v)


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    colors = {v for row in grid for v in row}
    if not colors <= {0, 1, 7}:
        errs.append(f"unexpected colors {sorted(colors - {0, 1, 7})}")
    rooms = _components(grid, 0)
    if len(rooms) < 2:
        errs.append("default floor plan should expose at least two rooms")
    doors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    if not doors:
        errs.append("default floor plan has no doors / no adjacency signal")
    for r, c in doors:
        vertical = 0 < r < h - 1 and grid[r - 1][c] == 0 and grid[r + 1][c] == 0
        horizontal = 0 < c < w - 1 and grid[r][c - 1] == 0 and grid[r][c + 1] == 0
        if not (vertical or horizontal):
            errs.append("door is not between exactly two neighbouring rooms")
            break
    return errs


def _draw_from_degenerate(name, rng):
    if name == "single_room":
        # one room -> 1x1 matrix [[0]]
        return _floor_plan(1, 1, 3, 3, {}, {})
    if name == "no_doors":
        # 2x2 rooms, no doors -> all-zero 4x4 matrix
        return _floor_plan(2, 2, 2, 2, {}, {})
    # fully_connected -> 2x2 rooms with every adjacent door
    dh = {(0, 0): 0, (1, 0): 0}
    dv = {(0, 0): 0, (0, 1): 0}
    return _floor_plan(2, 2, 2, 2, dh, dv)
