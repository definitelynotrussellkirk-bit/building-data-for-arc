"""Generator for arc_puzzle_bank_21_set21_s:S21_E1.

Rule: walls are colors {1,7,9}; the non-wall regions are rooms. Find the
room containing a color-2 marker; output keeps the walls, clears every
room to 0, and paints that target room 8.

This generator partitions the grid into wall-bounded rooms (a single
{1,7,9} wall color), drops one color-2 marker in one room, and optional
ignored decoys elsewhere.

Combinatorial axes: grid size, the wall layout, the wall color, the target
room, and the decoys.
Degenerates: no_seed, no_walls, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c1d80c25a99"
VERSION = "2.0.0"  # diversity: random wall-partitioned rooms + one color-2 target (was fixed ~24)
TASK_ID = "4c1d80c25a99"
SUMMARY = (
    "Wall-partitioned grid (size varies); walls are a color from {1,7,9} and "
    "the non-wall regions are rooms. One room holds a color-2 marker. Rule: "
    "keep the walls, clear every room to 0, and paint the marked room 8. The "
    "grid size, wall layout/color, target room and decoys vary freely (was a "
    "fixed setup, ~24 distinct)."
)

INVARIANTS = [
    "walls are a single color from {1,7,9}; rooms are the non-wall regions",
    "exactly one room contains a color-2 marker (the target)",
    "the output keeps walls, clears rooms to 0, and paints the target room 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seed", "no_walls", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "wall_color":     {"type": "color", "default": "rng {1,7,9}", "valid": "1|7|9"},
    "n_rooms":        {"type": "int", "default": "varies", "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "room_partition", "valid": "room_partition"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_seed|no_walls|full_grid"},
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
        rooms = [((r0, r1), (c0, c1)) for (r0, r1) in row_segs for (c0, c1) in col_segs]
        if len(rooms) < 2:
            continue

        wall = rng.choice([1, 7, 9])
        g = full_grid(h, w, 0)
        for c in vw:
            for r in range(h):
                g[r][c] = wall
        for r in hw:
            for c in range(w):
                g[r][c] = wall

        # one target room gets a color-2 marker; others get optional decoys
        ti = rng.randrange(len(rooms))
        for idx, ((r0, r1), (c0, c1)) in enumerate(rooms):
            cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
            if idx == ti:
                r, c = rng.choice(cells); g[r][c] = 2
            elif rng.random() < 0.5:
                k = rng.randint(1, max(1, len(cells) // 2))
                for (r, c) in rng.sample(cells, min(k, len(cells))):
                    g[r][c] = rng.choice([3, 4, 5, 6])
        return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None):
    """Verify wall-partitioned room invariants for 4c1d80c25a99."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    # Color 2 (target marker) must be present
    if 2 not in flat:
        errs.append("color 2 (target marker) not present")
    # Wall colors are {1,7,9} — at least one must be present
    wall_colors = {v for v in flat if v in (1, 7, 9)}
    if not wall_colors:
        errs.append("no wall color (1, 7, or 9) found")
    # Background (0) rooms should exist
    if 0 not in flat:
        errs.append("no room (0) cells")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    for r in range(9):
        g[r][4] = 1
    g[2][1] = 2
    if name == "no_seed":
        g[2][1] = 0
        return g
    if name == "no_walls":
        return full_grid(9, 9, 0)
    if name == "full_grid":
        return full_grid(9, 9, 1)
    return g
