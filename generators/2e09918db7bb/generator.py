"""Generator for arc_puzzle_bank_21_set7_s:S7_H2.

Slide all non-wall objects in the direction encoded by the corner header.

Rule: cell (0,0) is a direction marker (1=left 2=right 3=up 4=down); the
marker is removed, color-8 cells are fixed walls, every other color slides
as a rigid 4-connected component until blocked by a wall / another object /
the grid edge.

Combinatorial axes: grid_h/w, direction, walls (count/shape/position),
objects (count/shape/color/position).
Degenerates: no_marker, no_objects, no_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e09918db7bb"
VERSION = "2.0.1"  # diversity: random grid + direction + walls + objects (was fixed 9x12 + 6 hardcoded variants)
TASK_ID = "2e09918db7bb"
SUMMARY = (
    "0-bg grid (size varies). Cell (0,0) is a DIRECTION MARKER "
    "(1=left, 2=right, 3=up, 4=down). Some color-8 cells form fixed "
    "WALLS (random line segments). Several colored polyominoes are "
    "scattered as separate components. Rule: drop the marker cell, then "
    "slide EVERY non-wall object as a rigid 4-connected component in the "
    "marker's direction until it is blocked by a wall, another object, "
    "or the grid edge (gravity settling, leading objects move first). "
    "Grid size, direction, wall layout and the object set all vary "
    "freely, and at least one object always has clear runway so the "
    "output differs from the input (was a fixed 9x12 grid with 6 "
    "hardcoded variants)."
)

INVARIANTS = [
    "cell (0,0) is a direction marker",
    "color-8 cells are fixed blockers",
    "other colored objects slide as whole components until blocked",
    "at least one object moves under the selected gravity direction",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_objects", "no_walls")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11 (easy 8, hard 11..13)", "valid": "8..13"},
    "grid_w":         {"type": "int", "default": "rng 11..14 (easy 10, hard 13..16)", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "variant":        {"type": "int", "default": "n/a (now random)", "valid": "0..5"},
    "palette_size":   {"type": "int", "default": "rng", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "marker_plus_walls_plus_objects",
                       "valid": "marker_plus_walls_plus_objects"},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "3..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_marker|no_objects|no_walls"},
}

_DIRS = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}
_OBJ_COLORS = [1, 2, 3, 4, 5, 6, 7, 9]


def _random_blob(rng, size, maxd=3):
    """Random connected polyomino of `size` cells, bbox <= maxd x maxd."""
    for _ in range(200):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        minr = min(r for r, c in cells); minc = min(c for r, c in cells)
        norm = [(r - minr, c - minc) for r, c in cells]
        if max(r for r, c in norm) < maxd and max(c for r, c in norm) < maxd:
            return norm
    return [(0, 0)]


def _free(g, cells, top, left):
    """True if all (top+r,left+c) AND their 8-neighbours are 0 and in-bounds."""
    H = len(g); W = len(g[0])
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if not (0 <= rr < H and 0 <= cc < W):
                    if dr == 0 and dc == 0:
                        return False          # body cell itself must be in-bounds
                    continue                  # neighbour OOB is fine (edge)
                if g[rr][cc] != 0:
                    return False
    return True


def _try_place(g, rng, cells, color):
    H = len(g); W = len(g[0])
    bh = max(r for r, c in cells) + 1
    bw = max(c for r, c in cells) + 1
    for _ in range(40):
        top = rng.randint(0, H - bh)
        left = rng.randint(0, W - bw)
        if top == 0 and left == 0:
            continue                          # keep clear of the (0,0) marker
        if _free(g, cells, top, left):
            for r, c in cells:
                g[top + r][left + c] = color
            return [(top + r, left + c) for r, c in cells]
    return None


def _can_step(g, cells, dr, dc):
    """True if translating the whole object once is legal (so the rule moves it)."""
    H = len(g); W = len(g[0]); cs = set(cells)
    for r, c in cells:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < H and 0 <= nc < W):
            return False
        if (nr, nc) not in cs and g[nr][nc] != 0:
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nobj, nwall = (8, 8), (10, 10), (2, 2), (1, 1)
    elif difficulty == "hard":
        hr, wr, nobj, nwall = (11, 13), (13, 16), (3, 4), (2, 3)
    else:
        hr, wr, nobj, nwall = (9, 11), (11, 14), (2, 3), (1, 2)

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        marker = rng.randint(1, 4)
        dr, dc = _DIRS[marker]
        g = full_grid(h, w, 0)
        g[0][0] = marker

        # Walls: random color-8 line segments.
        for _ in range(rng.randint(*nwall)):
            length = rng.randint(2, 5)
            if rng.random() < 0.5:            # horizontal
                seg = [(0, j) for j in range(length)]
            else:                             # vertical
                seg = [(j, 0) for j in range(length)]
            _try_place(g, rng, seg, 8)

        # Objects: distinct-coloured polyominoes, each a separate component.
        palette = [c for c in _OBJ_COLORS if c != marker]
        rng.shuffle(palette)
        n = rng.randint(*nobj)
        objs = []
        for i in range(n):
            blob = _random_blob(rng, rng.randint(2, 5))
            placed = _try_place(g, rng, blob, palette[i % len(palette)])
            if placed:
                objs.append(placed)

        # Require >=1 object with clear runway, so the rule visibly moves it.
        if objs and any(_can_step(g, cells, dr, dc) for cells in objs):
            return g

    return g                                   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 12, 0)
    if name == "no_marker":
        # walls and objects without (0,0) marker → no slide direction
        for r in range(3, 8):
            g[r][5] = 8
        for r, c in [(1, 2), (1, 3), (2, 2)]:
            g[r][c] = 5
        return g
    if name == "no_objects":
        # marker and walls only → nothing to slide
        g[0][0] = 4
        for r in range(3, 8):
            g[r][5] = 8
        return g
    if name == "no_walls":
        # marker and objects without color-8 walls → objects slide off the edge
        g[0][0] = 4
        for r, c in [(1, 2), (1, 3), (2, 2)]:
            g[r][c] = 5
        for r, c in [(2, 8), (3, 8), (3, 9)]:
            g[r][c] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if grid[0][0] not in (1, 2, 3, 4):
        errors.append("cell (0,0) must be a direction marker 1..4")
    walls = sum(v == 8 for row in grid for v in row)
    objs = sum(v not in (0, 8) for r, row in enumerate(grid) for c, v in enumerate(row) if not (r == 0 and c == 0))
    if walls == 0:
        errors.append("default instance should include at least one color-8 wall")
    if objs == 0:
        errors.append("default instance should include at least one movable object cell")
    return errors
