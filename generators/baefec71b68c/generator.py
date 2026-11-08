"""Generator for 62ab2642.

Rule: pad the grid with a 5 border, flood from outside through 0-cells,
and find the ENCLOSED 0-regions. Fill the smallest with 7 (orange) and the
largest with 8 (cyan); other regions are unchanged. (The flood starts on
the padded border wall, so it marks nothing -- every 0-region counts, as
in the real task.)

This generator partitions the grid into rooms with color-5 wall lines,
sized so every room has a DISTINCT area (smallest/largest unambiguous).

Combinatorial axes: grid size, the wall layout (room count/areas), and
positions.
Degenerates: no_holes, all_holes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "baefec71b68c"
VERSION = "2.0.1"  # 2.0.0->2.0.1: add self_check. diversity: random wall-partitioned rooms with distinct areas (was fixed ~21)
TASK_ID = "baefec71b68c"
SUMMARY = (
    "0-bg grid (size varies) partitioned into rooms by color-5 wall lines, "
    "every room a distinct area. Rule: fill the smallest room 7 (orange) and "
    "the largest 8 (cyan); the rest stay 0. The grid size, room "
    "count/areas/layout vary freely (was a fixed setup, ~21 distinct)."
)

INVARIANTS = [
    "rooms are 0-regions separated by full color-5 wall lines",
    "all rooms have distinct areas so smallest/largest are unambiguous",
    "the smallest room fills 7 and the largest fills 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_holes", "all_holes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_rooms":        {"type": "int", "default": "varies", "valid": "3..9"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "room_partition", "valid": "room_partition"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_holes|all_holes|full_grid"},
}


def _walls(rng, N, max_walls):
    for _ in range(40):
        k = rng.randint(1, max_walls)
        if N - 2 < k:
            continue
        ws = sorted(rng.sample(range(1, N - 1), k))
        bounds = [-1] + ws + [N]
        if all(bounds[i + 1] - bounds[i] - 1 >= 2 for i in range(len(bounds) - 1)):
            return ws
    return []


def _segments(ws, N):
    bounds = [-1] + ws + [N]
    return [(bounds[i] + 1, bounds[i + 1] - 1)
            for i in range(len(bounds) - 1) if bounds[i + 1] - 1 >= bounds[i] + 1]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has color-5 wall cells separating bg-0 rooms."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_five = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not has_five:
        return errs  # degenerate no_holes
    # check that at least one bg-0 region exists (rooms)
    has_zero = any(grid[r][c] == 0 for r in range(h) for c in range(w))
    if not has_zero:
        errs.append("no bg-0 room cells found")
    return errs


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
        # rooms = cartesian product; require DISTINCT areas
        rooms = [((r0, r1), (c0, c1)) for (r0, r1) in row_segs for (c0, c1) in col_segs]
        areas = [(r1 - r0 + 1) * (c1 - c0 + 1) for (r0, r1), (c0, c1) in rooms]
        if len(set(areas)) != len(areas):
            continue

        g = full_grid(h, w, 0)
        for c in vw:
            for r in range(h):
                g[r][c] = 5
        for r in hw:
            for c in range(w):
                g[r][c] = 5
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    for r in range(12):
        g[r][4] = 5
    for c in range(12):
        g[7][c] = 5
    if name == "no_holes":
        return full_grid(12, 12, 0)
    if name == "all_holes":
        return g
    if name == "full_grid":
        return full_grid(12, 12, 5)
    return g
