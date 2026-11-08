"""Generator for arc_additional_puzzle_bank_volume7:H49.

Rule: the top two rows are a legend -- each column pairs a key color
(row 0) with a fill color (row 1). In the body (rows 2+), each region
reachable from a key-colored seed (through 0 or the seed's own color)
has its 0-cells filled with the mapped fill color.

This generator builds the legend plus framed rooms in the body, each
seeded with a key color, so its interior floods with the mapped fill.

Combinatorial axes: the legend pairs, the room shapes/seeds/keys, grid
size, and positions.
Degenerates: no_legend, no_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "2d08d999e513"
VERSION = "2.1.0"  # keep legend fill colors distinct from wall/key colors so filled rooms stay visually separable
TASK_ID = "2d08d999e513"
SUMMARY = (
    "Grid (size varies) whose top two rows are a key->fill LEGEND (column "
    "pairs). The body (rows 2+) has framed rooms, each seeded with a key "
    "color. Rule: each room's 0-cells flood with the mapped fill color. The "
    "legend pairs, room shapes/seeds/keys, grid size and positions vary "
    "freely (was a fixed setup, ~24 distinct)."
)

INVARIANTS = [
    "rows 0-1 are a legend of key (row 0) -> fill (row 1) column pairs",
    "each body room is wall-framed with a key-colored seed and 0-interior",
    "a room's 0-cells fill with the legend fill for its seed key",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_seeds", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_legend":       {"type": "int", "default": "varies", "valid": "2..4"},
    "n_rooms":        {"type": "int", "default": "varies", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "legend_then_rooms",
                       "valid": "legend_then_rooms"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legend|no_seeds|full_grid"},
}


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, lr, rr, ir = (10, 13), (12, 15), (2, 3), (1, 2), (2, 3)
    elif difficulty == "hard":
        hr, wr, lr, rr, ir = (16, 22), (16, 24), (3, 4), (2, 4), (3, 5)
    else:
        hr, wr, lr, rr, ir = (12, 17), (13, 19), (2, 4), (1, 3), (2, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        K = rng.randint(*lr)
        keys = rng.sample(range(1, 10), K)
        wall = rng.choice([c for c in range(1, 10) if c not in keys])
        fill_pool = [c for c in range(1, 10) if c not in set(keys + [wall])]
        fills = rng.sample(fill_pool, K)
        legend = dict(zip(keys, fills))

        g = full_grid(h, w, 0)
        # legend in the top two rows
        for i, k in enumerate(keys):
            g[0][i] = k
            g[1][i] = legend[k]

        occ = [[False] * w for _ in range(h)]
        for r in range(2):
            for c in range(w):
                occ[r][c] = True   # legend rows reserved

        placed = 0
        for _ in range(rng.randint(*rr)):
            ih = rng.randint(*ir); iw = rng.randint(*ir)
            fh = ih + 2; fw = iw + 2
            key = rng.choice(keys)
            for _t in range(40):
                if fh > h - 2 or fw > w:
                    break
                top = rng.randint(2, h - fh); left = rng.randint(0, w - fw)
                if _reserve(occ, top, left, fh, fw, h, w):
                    draw_frame(g, top, left, top + fh - 1, left + fw - 1, wall)
                    # seed: 1-2 cells of the key inside, rest 0
                    interior = [(top + 1 + r, left + 1 + c)
                                for r in range(ih) for c in range(iw)]
                    rng.shuffle(interior)
                    nseed = 1 if len(interior) <= 2 else rng.randint(1, min(2, len(interior) - 1))
                    for (r, c) in interior[:nseed]:
                        g[r][c] = key
                    placed += 1
                    break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    g[0][0] = 3; g[1][0] = 4
    g[0][1] = 6; g[1][1] = 7
    draw_frame(g, 3, 1, 6, 4, 5)
    g[4][2] = 3
    if name == "no_legend":
        g[0][0] = 0; g[1][0] = 0; g[0][1] = 0; g[1][1] = 0
        return g
    if name == "no_seeds":
        g[4][2] = 0
        return g
    if name == "full_grid":
        return full_grid(10, 12, 5)
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h < 5 or any(len(row) != w for row in grid):
        return ["grid must be rectangular with body rows"]
    pairs = [(grid[0][c], grid[1][c]) for c in range(w) if grid[0][c] or grid[1][c]]
    if len(pairs) < 2:
        errs.append("legend should contain at least two key->fill pairs")
    if any(k == 0 or f == 0 for k, f in pairs):
        errs.append("legend keys/fills should be nonzero")
    keys = [k for k, _ in pairs]
    fills = [f for _, f in pairs]
    if len(keys) != len(set(keys)):
        errs.append("legend keys should be unique")
    body_vals = [v for row in grid[2:] for v in row if v != 0]
    if not body_vals:
        errs.append("body should contain framed rooms and key seeds")
        return errs
    from collections import Counter
    wall = Counter(v for v in body_vals if v not in keys).most_common(1)[0][0]
    if wall in keys or wall in fills:
        errs.append("wall color should be distinct from legend keys and fills")
    seed_count = sum(1 for row in grid[2:] for v in row if v in keys)
    if seed_count < 1:
        errs.append("at least one room must contain a key-colored seed")
    if not any(v == 0 for row in grid[2:] for v in row):
        errs.append("rooms should have 0-cells for the fill rule to act on")
    return errs
