"""Generator for arc_additional_puzzles_21_set16_bundle:M112 — fill each room from its seed.

Rule: color-5 walls divide the grid into compartments (connected non-5 regions).
For each compartment that has exactly one non-{0,5} marker color, fill its empty
(0) cells with that color.

Prior flag: the generator used a FIXED 9x11 grid with a FIXED 2x2 lattice of 4
rooms (in_shapes 1, out_shapes 1). The rule is general — any lattice of rooms of
any size. This version varies grid size and the room lattice (RxC, varied room
dims), one marker per room.

Rule-safe diversity: grid size, lattice shape (rooms per row/col), room sizes,
marker colors/positions.
Degenerates: no_walls, no_markers, two_markers_one_chamber.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f4e7e99f60c9"
VERSION = "3.1.0"  # varied RxC room lattice + varied grid size (was fixed 9x11 / 2x2, in_shapes 1)
TASK_ID = "f4e7e99f60c9"
SUMMARY = (
    "Grid of color-5 WALLS forming an RxC lattice of sealed COMPARTMENTS (rooms), "
    "sizes/counts vary. Each room holds ONE marker cell in a non-{0,5} color. "
    "Rule: for each compartment with exactly one such color, fill its empty cells "
    "with it. Net: each room floods with its marker's color, bordered by gray "
    "walls. (Was: fixed 9x11 grid, fixed 2x2 lattice of 4 rooms.)"
)

INVARIANTS = [
    "color-5 walls form an RxC lattice of sealed rooms (each a separate region)",
    "each room has exactly one marker in a non-{0,5} color",
    "rooms are separated by 1-wide walls (distinct connected components)",
    "output fills each room's empty cells with its marker color",
]

PALETTE_KINDS = ("default", "warm_markers", "cool_markers", "varied_markers")
DEGENERATE_TEXTURES = ("no_walls", "no_markers", "two_markers_one_chamber")
HELPFUL_TEXTURES = PALETTE_KINDS
_MARK_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)   # non-0, non-5

AXES = {
    "rooms_r":  {"type": "int", "default": "2 easy / 2-3 med / 2-4 hard", "valid": "1..5"},
    "rooms_c":  {"type": "int", "default": "2 easy / 2-3 med / 2-4 hard", "valid": "1..5"},
    "room_h":   {"type": "int", "default": "room interior 2-4", "valid": "2..6"},
    "room_w":   {"type": "int", "default": "room interior 2-4", "valid": "2..6"},
    "n_distinct_colors": {"type": "int", "default": "<= rooms", "valid": "1..8"},
    "density":  {"type": "str", "default": "rooms", "valid": "rooms"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        rr, cr, rhr, rwr = (2, 2), (2, 2), (2, 3), (3, 4)
    elif difficulty == "hard":
        rr, cr, rhr, rwr = (2, 4), (2, 4), (2, 4), (2, 5)
    else:
        rr, cr, rhr, rwr = (2, 3), (2, 3), (2, 4), (2, 4)
    rng = ctx.draw_rng("layout")
    nr = rng.randint(*rr); nc = rng.randint(*cr)
    rh = rng.randint(*rhr); rw = rng.randint(*rwr)
    if nr * nc < 2:                       # need >=2 rooms
        nc = 2
    H = 1 + nr * (rh + 1)
    W = 1 + nc * (rw + 1)
    g = full_grid(H, W, 5)
    cols = list(_MARK_COLORS); rng.shuffle(cols)
    k = 0
    for i in range(nr):
        for j in range(nc):
            top = 1 + i * (rh + 1); left = 1 + j * (rw + 1)
            for r in range(top, top + rh):
                for c in range(left, left + rw):
                    g[r][c] = 0
            # one marker per room (colors may repeat if rooms > 8)
            mr = rng.randint(top, top + rh - 1); mc = rng.randint(left, left + rw - 1)
            g[mr][mc] = cols[k % len(cols)]
            k += 1
    return g


def _non_wall_regions(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); regions = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 5:
                        seen.add((nr, nc)); stack.append((nr, nc))
            regions.append(cells)
    return regions


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)) or any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errs.append("outer border must be all color-5 wall")
    regions = _non_wall_regions(grid)
    if len(regions) < 2:
        errs.append(f"expected at least two sealed rooms, found {len(regions)}")
    for i, cells in enumerate(regions):
        vals = [grid[r][c] for r, c in cells]
        markers = [v for v in vals if v not in (0, 5)]
        if len(markers) != 1:
            errs.append(f"room {i} has {len(markers)} markers, expected exactly 1")
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        if len(cells) != (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1):
            errs.append(f"room {i} is not rectangular")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    if name == "no_walls":
        g = full_grid(h, w, 0)
        for sr, sc, v in [(2, 2, 4), (2, 7, 6), (6, 2, 7), (6, 8, 9)]:
            g[sr][sc] = v
        return g
    g = full_grid(h, w, 5)
    for r0 in (1, 5):
        for c0 in (1, 6):
            for r in range(r0, r0 + 3):
                for c in range(c0, c0 + 4):
                    if r < h - 1 and c < w - 1:
                        g[r][c] = 0
    if name == "no_markers":
        return g
    if name == "two_markers_one_chamber":
        g[2][2] = 4; g[2][3] = 6   # two markers in one room -> not filled
        g[2][7] = 7; g[6][2] = 8; g[6][8] = 9
        return g
    return g
