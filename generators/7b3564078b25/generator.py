"""Generator for arc_additional_puzzle_bank_volume12:H84.

Rule: color 5 is a wall; each non-5 chamber's interior markers (colors
1-4) vote. A chamber's 0-cells fill with the strict-majority marker color
ONLY IF the marker count is EVEN (and a strict majority exists); odd count
or a tie leaves the chamber's 0-cells empty.

This generator partitions the grid into color-5-walled rooms and seeds
each with interior markers -- some with an even count + strict majority
(fill), some odd or tied (no fill).

Combinatorial axes: grid size, the wall layout, and the per-room marker
counts/colors (parity + plurality).
Degenerates: no_walls, no_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7b3564078b25"
VERSION = "2.0.1"
TASK_ID = "7b3564078b25"
SUMMARY = (
    "Color-5 wall field (size varies) partitioned into rooms, each seeded "
    "with interior {1,2,3,4} markers. Rule: a room's 0-cells fill with the "
    "strict-majority marker color only if the marker count is EVEN (odd or "
    "tie -> empty). The grid size, wall layout and per-room marker "
    "counts/colors vary freely (was a fixed setup, ~23 distinct)."
)

INVARIANTS = [
    "rooms are non-5 regions separated by full color-5 wall lines",
    "markers (colors 1-4) live inside the rooms with 0-cells to fill",
    "fill happens only on an even marker count with a strict majority",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_rooms":        {"type": "int", "default": "varies", "valid": "2..9"},
    "marker_parity":  {"type": "str", "default": "even|odd", "valid": "even|odd"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "room_partition", "valid": "room_partition"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_walls|no_markers|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-5 wall cell, ≥1 non-5 nonzero cell (room marker)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    has_wall = any(v == 5 for row in grid for v in row)
    has_marker = any(1 <= v <= 4 for row in grid for v in row)
    errs = []
    if not has_wall:
        errs.append("expected color-5 wall cells; found none")
    if not has_marker:
        errs.append("expected interior marker cells (1-4); found none")
    return errs


def _walls(rng, N, max_walls):
    for _ in range(40):
        k = rng.randint(1, max_walls)
        if N - 2 < k:
            continue
        ws = sorted(rng.sample(range(1, N - 1), k))
        bounds = [-1] + ws + [N]
        if all(bounds[i + 1] - bounds[i] - 1 >= 3 for i in range(len(bounds) - 1)):
            return ws
    return []


def _segments(ws, N):
    bounds = [-1] + ws + [N]
    return [(bounds[i] + 1, bounds[i + 1] - 1)
            for i in range(len(bounds) - 1) if bounds[i + 1] - 1 >= bounds[i] + 1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, mw = (12, 15), (12, 15), 2
    elif difficulty == "hard":
        hr, wr, mw = (18, 24), (18, 24), 3
    else:
        hr, wr, mw = (14, 19), (14, 19), 2

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        vw = _walls(rng, w, mw); hw = _walls(rng, h, mw)
        col_segs = _segments(vw, w); row_segs = _segments(hw, h)
        if len(col_segs) * len(row_segs) < 2:
            continue

        g = full_grid(h, w, 0)
        for c in vw:
            for r in range(h):
                g[r][c] = 5
        for r in hw:
            for c in range(w):
                g[r][c] = 5

        filled = 0
        for (r0, r1) in row_segs:
            for (c0, c1) in col_segs:
                cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
                area = len(cells)
                rng.shuffle(cells)
                if rng.random() < 0.7 and area >= 3:        # even count + strict majority -> fill
                    win = rng.randint(1, 4)
                    nwin, nlose = rng.choice([(2, 0), (4, 0), (3, 1)])
                    total = nwin + nlose
                    if total > area - 1:
                        nwin, nlose, total = 2, 0, 2
                    if total > area - 1:
                        continue
                    other = rng.choice([x for x in (1, 2, 3, 4) if x != win])
                    for (r, c) in cells[:nwin]:
                        g[r][c] = win
                    for (r, c) in cells[nwin:nwin + nlose]:
                        g[r][c] = other
                    filled += 1
                elif area >= 2:                             # odd count -> no fill
                    k = rng.choice([1, 3])
                    if k > area - 1:
                        k = 1
                    for (r, c) in cells[:k]:
                        g[r][c] = rng.randint(1, 4)
        if filled >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    for r in range(9):
        g[r][4] = 5
    if name == "no_walls":
        return full_grid(9, 9, 0)
    if name == "no_markers":
        return g
    if name == "full_grid":
        return full_grid(9, 9, 5)
    g[1][1] = 2; g[3][2] = 2          # even (2) majority 2 -> fill left room
    g[1][6] = 3                        # odd (1) -> no fill right room
    return g
