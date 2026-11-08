"""Generator for arc_puzzle_bank_21_set21_s:S21_M2 — BFS through rooms via doors.

Rule: walls (color 1) divide the grid into rooms. Some wall cells are
'doors' (color 7) connecting adjacent rooms. One room has a color-2
seed. Rule: do BFS over rooms (rooms connected by a door are
adjacent). Color the room interiors per BFS distance from the seed
room: d=0 → 2, d=1 → 3, d=2 → 4, else → 5. Walls stay 1, doors
stay 7.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1dbed5788bcc"
VERSION = "2.1.1"  # oversize fix: trim rooms so nrr/ncc grid fits 30x30 (hard reached w=31 -> clipped/corrupt)
TASK_ID = "1dbed5788bcc"

SUMMARY = (
    "Color-1 (blue) grid wall partitioning the canvas "
    "(h = nrr*(rh+1)+1, w = ncc*(rw+1)+1; "
    "nrr=2-4 rooms vertically, ncc=2-5 rooms "
    "horizontally; each room is rh×rw interior cells "
    "of 0). The blue walls form a regular "
    "ROOM GRID with carved 0-interiors. SOME WALL "
    "CELLS between adjacent rooms are DOORS (color 7) "
    "placed with probability 0.7 per adjacency. ONE "
    "ROOM contains a single color-2 (red) SEED MARKER "
    "at a random position inside. Rule: build the "
    "ROOM ADJACENCY GRAPH where two rooms are "
    "connected if a color-7 DOOR cell lies on their "
    "shared wall. Run BFS from the seed's room. For "
    "each room, FILL its 0-interior cells based on "
    "BFS distance: d=0 → 2 (red), d=1 → 3 (green), "
    "d=2 → 4 (yellow), d≥3 → 5 (gray). Walls and "
    "doors are preserved. Net: rooms are flood-"
    "filled by graph distance through doors."
)

# Rivals: 'output is input' refuted by demos (rooms fill with 2/3/4/5).
# 'fill by spatial distance' refuted by demos where door layout
# changes graph distance. 'use seed color for all' refuted by demos
# with multiple distances. 'walls become rooms' refuted by demos
# (walls stay 1). 4 demos to cover distances 0, 1, 2, 3+.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "color 1 wall grid forms a regular partition into rooms",
    "≥3 rooms total so distance values span 0..2 or more",
    "exactly one color-2 seed in one room",
    "color-7 door cells exist on wall edges between adjacent rooms",
]

AXES = {
    "n_room_rows": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "n_room_cols": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "room_h":      {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "room_w":      {"type": "int", "default": "rng 3..4", "valid": "2..5"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        nrr = rng.randint(2, 2); ncc = rng.randint(2, 3)
        rh = rng.randint(3, 3); rw = rng.randint(3, 3)
    elif difficulty == "hard":
        nrr = rng.randint(3, 4); ncc = rng.randint(3, 5)
        rh = rng.randint(3, 5); rw = rng.randint(3, 5)
    else:
        nrr = rng.randint(2, 3); ncc = rng.randint(3, 4)
        rh = rng.randint(3, 4); rw = rng.randint(3, 4)

    h = nrr * rh + nrr + 1
    w = ncc * rw + ncc + 1
    # trim rooms so the grid fits 30x30 (hard ncc*rw reached w=31 -> clipped/corrupt)
    while w > 30 and ncc > 1:
        ncc -= 1; w = ncc * rw + ncc + 1
    while h > 30 and nrr > 1:
        nrr -= 1; h = nrr * rh + nrr + 1
    g = full_grid(h, w, 1)
    # Carve room interiors with 0
    room_top = []
    for ri in range(nrr):
        for ci in range(ncc):
            r0 = ri * (rh + 1) + 1
            c0 = ci * (rw + 1) + 1
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + rw):
                    g[r][c] = 0
            room_top.append((ri, ci, r0, c0))
    # Add door cells (7) on each pair of adjacent rooms (horizontal and
    # vertical adjacency). Each adjacency gets a door with high prob.
    for ri, ci, r0, c0 in room_top:
        # Right neighbor door (at col c0 + rw, somewhere in interior rows)
        if ci < ncc - 1 and rng.random() < 0.7:
            door_r = r0 + rng.randint(0, rh - 1)
            door_c = c0 + rw
            g[door_r][door_c] = 7
        # Down neighbor door (at row r0 + rh, somewhere in interior cols)
        if ri < nrr - 1 and rng.random() < 0.7:
            door_r = r0 + rh
            door_c = c0 + rng.randint(0, rw - 1)
            g[door_r][door_c] = 7
    # Place color-2 seed in a random room
    seed_room = rng.randrange(nrr * ncc)
    _, _, r0, c0 = room_top[seed_room]
    sr = r0 + rng.randint(0, rh - 1)
    sc = c0 + rng.randint(0, rw - 1)
    g[sr][sc] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-1 wall cells; exactly one color-2 seed; color-7 door cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    c7 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 7)
    if c1 == 0:
        errs.append("no color-1 wall cells")
    if c2 != 1:
        errs.append(f"expected exactly 1 color-2 seed, found {c2}")
    if c7 == 0:
        errs.append("no color-7 door cells")
    return errs
