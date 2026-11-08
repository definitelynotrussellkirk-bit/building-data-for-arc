"""Generator for 3ad05f52 — maze with marker, ray-fill + wide-zone bridge.

Rule (per the canonical Racket): the input has cyan(8) walls forming a maze
structure plus a single marker color (a 3x3 block) inside one of the rooms.
The output fills:
  * cells reachable from the marker by cardinal "rays" that terminate at walls
    (or grid edges if the corresponding row/col contains walls)
  * cells in "wide" cols/rows (cols/rows with no walls) between the min and
    max painted rows/cols — the "min fill in the SUPER WIDE gap"

Per-puzzle variation: random grid size, random maze patch placement,
random marker color and position.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paste, set_cell

GENERATOR_ID = "10a669379137"
VERSION = "2.3.0"  # guarantee the marker sits in a room with >=1 open doorway so rays always escape (fixes enclosed-room identity outputs)
TASK_ID = "10a669379137"
SUMMARY = (
    "Cyan(8) maze walls + single 3x3 marker block. Output fills via cardinal "
    "ray-expansion bounded by walls, plus wide-axis bridge fill between "
    "min/max painted positions in wall-less cols/rows."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one wall color (most-frequent non-bg) and exactly one marker color",
    "the maze structure forms at least one bounded room containing the marker",
    "marker is a 3x3 solid block inside a wall-bounded room",
]

AXES = {
    "rooms_r":     {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "rooms_c":     {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "grid_size":   {"type": "int", "default": "patch_h+3..+8", "valid": "14..30"},
    "marker_color": {"type": "int", "default": "rng 1..9", "valid": "1..9 except 8"},
}

def _build_maze(rng, rooms_r, rooms_c):
    """Construct an 8-wall maze patch: a rooms_r x rooms_c grid of 3x3 rooms
    separated by 1-wide walls, full outer wall, with randomized 1-cell
    doorways punched between some adjacent rooms. Returns (patch, room_origins)
    where room_origins are the (r, c) top-left corners of each 3x3 room."""
    ph = rooms_r * 3 + (rooms_r + 1)
    pw = rooms_c * 3 + (rooms_c + 1)
    patch = [[8] * pw for _ in range(ph)]
    room_origins = []
    for ri in range(rooms_r):
        for ci in range(rooms_c):
            r0 = 1 + ri * 4
            c0 = 1 + ci * 4
            room_origins.append((r0, c0))
            for r in range(r0, r0 + 3):
                for c in range(c0, c0 + 3):
                    patch[r][c] = 0
    # Track which rooms (flat index ri*rooms_c+ci) got >=1 open doorway so the
    # marker can be placed in a connected room; a fully-enclosed marker room
    # yields rays that hit walls immediately → output == input (degenerate).
    connected = set()

    def mark(ri, ci):
        connected.add(ri * rooms_c + ci)

    # Vertical-wall doorways (between horizontally adjacent rooms): wall col is
    # c0+3; punch a gap at one of the 3 room rows.
    for ri in range(rooms_r):
        for ci in range(rooms_c - 1):
            if rng.random() < 0.7:
                r0 = 1 + ri * 4
                wall_c = 1 + ci * 4 + 3
                gap = r0 + rng.randint(0, 2)
                patch[gap][wall_c] = 0
                mark(ri, ci); mark(ri, ci + 1)
    # Horizontal-wall doorways (between vertically adjacent rooms).
    for ri in range(rooms_r - 1):
        for ci in range(rooms_c):
            if rng.random() < 0.7:
                c0 = 1 + ci * 4
                wall_r = 1 + ri * 4 + 3
                gap = c0 + rng.randint(0, 2)
                patch[wall_r][gap] = 0
                mark(ri, ci); mark(ri + 1, ci)
    # Guarantee at least one doorway exists (so >=1 connected room): if every
    # probabilistic punch missed, force one vertical doorway between rooms 0,0-0,1.
    if not connected:
        wall_c = 1 + 0 * 4 + 3
        gap = 1 + rng.randint(0, 2)
        patch[gap][wall_c] = 0
        mark(0, 0); mark(0, 1)
    return patch, room_origins, sorted(connected)


def _stamp_marker(g, anchor_r, anchor_c, color):
    for dr in range(3):
        for dc in range(3):
            set_cell(g, anchor_r + dr, anchor_c + dc, color)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants for the maze + marker input. Crucially verifies the
    marker room has an open doorway (a 0 cardinally adjacent to the 3x3 block) so
    the rule's rays escape and the output is not identical to the input."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    colors = {}
    for r in range(h):
        for c in range(w):
            colors.setdefault(grid[r][c], 0)
            colors[grid[r][c]] = colors[grid[r][c]] + 1
    if 8 not in colors:
        errors.append("expected cyan(8) maze walls")
    marker_colors = [v for v in colors if v not in (0, 8)]
    if len(marker_colors) != 1:
        return errors + [f"expected exactly one marker color, found {marker_colors}"]
    mc = marker_colors[0]
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == mc]
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if (r1 - r0, c1 - c0) != (2, 2) or len(cells) != 9:
        errors.append(f"marker must be a solid 3x3 block, got {len(cells)} cells "
                      f"spanning {(r1 - r0 + 1, c1 - c0 + 1)}")
        return errors
    # doorway check: a 0 immediately outside the block on a cardinal edge.
    escape = False
    for c in range(c0, c1 + 1):
        if r0 - 1 >= 0 and grid[r0 - 1][c] == 0:
            escape = True
        if r1 + 1 < h and grid[r1 + 1][c] == 0:
            escape = True
    for r in range(r0, r1 + 1):
        if c0 - 1 >= 0 and grid[r][c0 - 1] == 0:
            escape = True
        if c1 + 1 < w and grid[r][c1 + 1] == 0:
            escape = True
    if not escape:
        errors.append("marker room is fully enclosed (no doorway) — rays cannot "
                      "escape and the rule output would equal the input")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        rooms_r = ctx.draw_int("rooms_r", 2, 2)
        rooms_c = ctx.draw_int("rooms_c", 2, 2)
    elif difficulty == "hard":
        rooms_r = ctx.draw_int("rooms_r", 2, 4)
        rooms_c = ctx.draw_int("rooms_c", 3, 5)
    else:
        rooms_r = ctx.draw_int("rooms_r", 2, 3)
        rooms_c = ctx.draw_int("rooms_c", 2, 4)

    patch, room_origins, connected = _build_maze(rng, rooms_r, rooms_c)
    patch_h = len(patch)
    patch_w = len(patch[0])

    H = ctx.draw_int("grid_size", patch_h + 3, patch_h + 8)
    W = patch_w + rng.randint(2, 6)
    H = max(14, min(30, max(H, patch_h + 2)))
    W = max(14, min(30, max(W, patch_w + 2)))

    patch_r = rng.randint(1, H - patch_h - 1)
    patch_c = rng.randint(1, W - patch_w - 1)

    g = full_grid(H, W, 0)
    paste(g, patch, patch_r, patch_c)

    marker_color = ctx.draw_int("marker_color", 1, 9)
    if marker_color == 8:
        marker_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])

    # place the marker only in a room that has an open doorway, else its rays
    # cannot escape and the rule output equals the input.
    room_local = rng.choice([room_origins[i] for i in connected])
    marker_r = patch_r + room_local[0]
    marker_c = patch_c + room_local[1]
    _stamp_marker(g, marker_r, marker_c, marker_color)

    return g
