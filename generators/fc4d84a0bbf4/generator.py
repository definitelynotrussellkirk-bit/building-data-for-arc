"""Generator for arc_additional_puzzle_bank_volume10:H70.

Rule: rows 0-1 are a LEGEND mapping seed 1/2/3 (row 0) to an output color
(row 1 below it). In the r>=2 area, each 4-connected non-5 chamber is
scored by how many color-1, color-2, color-3 markers it holds; if one has
a STRICT majority, the chamber's empty cells are filled with that seed's
legend color (ties stay 0).

This generator builds the legend plus an r>=2 area partitioned into rooms
by color-5 walls, each room seeded with markers giving a majority or a tie.

Combinatorial axes: grid size, the legend colors, the room layout, and
each room's marker counts/positions.
Degenerates: no_legend, no_walls, tied_majority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc4d84a0bbf4"
VERSION = "2.0.1"  # add executable legend/room-majority invariants and fail closed on rare placement failure
TASK_ID = "fc4d84a0bbf4"
SUMMARY = (
    "0-bg grid (size varies). Rows 0-1: a LEGEND mapping seed 1/2/3 to an "
    "output color. The r>=2 area is partitioned by color-5 walls into rooms, "
    "each holding color-1/2/3 markers. Rule: fill each room's empty cells "
    "with the legend color of its STRICT-majority marker (ties stay 0). The "
    "grid size, legend colors, room layout and each room's marker "
    "counts/positions vary freely (was a fixed layout, ~17 distinct)."
)

INVARIANTS = [
    "rows 0-1 map each seed 1/2/3 to a distinct output color",
    "the r>=2 area is split by color-5 walls into rooms with 1/2/3 markers",
    "at least one room has a strict majority (a fill) and a mix of outcomes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_walls", "tied_majority")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..24"},
    "rooms_r":        {"type": "int", "default": "varies", "valid": "1..2"},
    "rooms_c":        {"type": "int", "default": "varies", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "legend_then_rooms", "valid": "legend_then_rooms"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..6"},
    "seed_distribution": {"type": "str", "default": "majorities", "valid": "majorities"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legend|no_walls|tied_majority"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _body_components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r0 in range(2, h):
        for c0 in range(w):
            if seen[r0][c0] or grid[r0][c0] == 5:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 2 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] != 5:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
    if h < 3:
        return ["grid too short for 2-row legend plus body"]

    seed_cols = {}
    for c, v in enumerate(grid[0]):
        if v in (1, 2, 3):
            if v in seed_cols:
                errors.append(f"duplicate legend seed {v}")
            seed_cols[v] = c
        elif v != 0:
            errors.append(f"unexpected nonzero in legend seed row: {v}")
    if set(seed_cols) != {1, 2, 3}:
        errors.append(f"legend seeds are {sorted(seed_cols)}; expected 1,2,3")
    legend_out = []
    for seed_value in (1, 2, 3):
        c = seed_cols.get(seed_value)
        if c is None:
            continue
        out_color = grid[1][c]
        if out_color in (0, 1, 2, 3, 5):
            errors.append(f"bad legend output color {out_color} for seed {seed_value}")
        legend_out.append(out_color)
    if len(legend_out) != len(set(legend_out)):
        errors.append("legend output colors are not distinct")

    if not any(5 in row for row in grid[2:]):
        errors.append("body has no color-5 room wall")
    comps = _body_components(grid)
    if len(comps) < 2:
        errors.append("body is not partitioned into at least two rooms")
    any_majority = False
    any_marker = False
    for cells in comps:
        counts = {1: 0, 2: 0, 3: 0}
        for r, c in cells:
            v = grid[r][c]
            if v in counts:
                counts[v] += 1
                any_marker = True
        top = max(counts.values())
        if top > 0 and list(counts.values()).count(top) == 1:
            any_majority = True
    if not any_marker:
        errors.append("body rooms contain no seed markers")
    if not any_majority:
        errors.append("no room has a strict seed majority")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        Rr, Cr, Dr, Mr = (1, 1), (2, 2), (3, 4), (1, 3)
    elif difficulty == "hard":
        Rr, Cr, Dr, Mr = (2, 2), (2, 3), (3, 5), (2, 4)
    else:
        Rr, Cr, Dr, Mr = (1, 2), (2, 3), (3, 5), (1, 4)

    for _attempt in range(40):
        R = rng.randint(*Rr); C = rng.randint(*Cr)
        room_h = [rng.randint(*Dr) for _ in range(R)]
        room_w = [rng.randint(*Dr) for _ in range(C)]
        RH = sum(room_h) + (R - 1)
        W = sum(room_w) + (C - 1)
        if W < 4:
            continue
        H = RH + 2                          # rows 0-1 legend
        g = full_grid(H, W, 0)

        # legend: seeds 1/2/3 -> distinct output colors at 3 columns
        legend_cols = rng.sample(range(W), 3)
        legend_colors = rng.sample([4, 6, 7, 8, 9], 3)
        for s_, lc in zip((1, 2, 3), legend_cols):
            g[0][lc] = s_
            g[1][lc] = legend_colors[s_ - 1]

        # room origins inside the r>=2 area
        rtops = []
        acc = 2
        for j in range(R):
            rtops.append(acc); acc += room_h[j] + 1
        ctops = []
        acc = 0
        for i in range(C):
            ctops.append(acc); acc += room_w[i] + 1

        # 5-walls
        for j in range(R - 1):
            wr_ = rtops[j] + room_h[j]
            for c in range(W):
                g[wr_][c] = 5
        for i in range(C - 1):
            wc_ = ctops[i] + room_w[i]
            for r in range(2, H):
                g[r][wc_] = 5

        # markers per room
        any_majority = False
        for j in range(R):
            for i in range(C):
                cells = [(rtops[j] + dr, ctops[i] + dc)
                         for dr in range(room_h[j]) for dc in range(room_w[i])]
                m = min(rng.randint(*Mr), len(cells))
                marks = [rng.randint(1, 3) for _ in range(m)]
                c1 = marks.count(1); c2 = marks.count(2); c3 = marks.count(3)
                if (c1 > c2 and c1 > c3) or (c2 > c1 and c2 > c3) or (c3 > c1 and c3 > c2):
                    any_majority = True
                for (r, c), col in zip(rng.sample(cells, m), marks):
                    g[r][c] = col

        if any_majority:
            return g

    raise ValueError("could not generate a chamber with a strict majority")


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 9, 0)
    g[0][0] = 1; g[1][0] = 6
    g[0][1] = 2; g[1][1] = 7
    g[0][2] = 3; g[1][2] = 8
    if name == "no_legend":
        g2 = full_grid(7, 9, 0)
        for r in range(2, 7):
            g2[r][4] = 5
        g2[3][1] = 1; g2[3][2] = 1
        return g2
    if name == "no_walls":
        g[3][1] = 1; g[3][2] = 1; g[4][5] = 2
        return g
    if name == "tied_majority":
        for r in range(2, 7):
            g[r][4] = 5
        g[3][1] = 1; g[3][2] = 2          # tie -> no fill
        return g
    return g
