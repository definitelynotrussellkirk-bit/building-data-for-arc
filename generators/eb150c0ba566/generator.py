"""Generator for arc_puzzle_bank_seventh21:H45 — prototype-stamp expansion.

Rule: the HEADER (rows 0-2) holds two 3x3 PROTOTYPE shapes -- proto2 in
columns 0-2 (color 2) and proto3 in columns 4-6
(color 3) -- with column 3 a separator and row 3 a full divider. Below
the divider (rows 4+) are SEED cells (single 2s and 3s). For each seed of
color C at (r, c), STAMP the matching prototype's C-cells at offset
(r+dr, c+dc). The header is copied verbatim; the seed area is rebuilt
from the stamps.

Combinatorial axes: prototype shapes, grid size, seed count/positions/
colors.
Degenerates: no_seeds, single_seed, no_header.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eb150c0ba566"
VERSION = "2.2.0"  # accept canonical zero-at-origin prototypes, exercise seed-erasure cases, and reject impossible exact seed-count overrides instead of silently under-placing
TASK_ID = "eb150c0ba566"

SUMMARY = (
    "Grid (w>=7) with a HEADER: rows 0-2 hold two 3x3 PROTOTYPE shapes -- "
    "proto2 (color 2) in cols 0-2 and proto3 (color 3) in cols 4-6, with "
    "col 3 = 9 separator -- and row 3 is a full color-9 divider. Below the "
    "divider (rows 4+) are SEED cells: single 2s and 3s at separated "
    "positions (3x3 stamp footprint fits, non-overlapping). Rule: for each "
    "seed of color C, stamp the matching prototype's C-cells at the seed's "
    "offset; the header copies verbatim. Net: each seed expands into its "
    "color's prototype shape."
)

INVARIANTS = [
    "rows 0-2 hold proto2 (color 2, cols 0-2) and proto3 (color 3, cols 4-6); col3=9",
    "row 3 is a full color-9 divider",
    "each prototype is a nonempty 3x3 mask over background and its own color",
    "seeds below the divider are single 2s/3s whose 3x3 stamp fits and don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "no_header")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14 by diff", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 7..14 by diff", "valid": "7..16"},
    "n_seeds":        {"type": "int", "default": "rng 2..6 by diff", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "header_protos_plus_seeds",
                       "valid": "header_protos_plus_seeds"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_seeds|single_seed|no_header"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _make_proto(rng, color):
    """Connected nonempty 3x3 mask over ``{0, color}``.

    The canonical authority does not require the prototype's top-left cell to
    be colored.  Sampling the growth origin across all nine cells deliberately
    includes cases where stamping erases the visible seed marker.
    """
    cells = {(rng.randrange(3), rng.randrange(3))}
    target = rng.randint(3, 6)
    for _ in range(60):
        if len(cells) >= target:
            break
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            cells.add((nr, nc))
    p = [[0, 0, 0] for _ in range(3)]
    for (r, c) in cells:
        p[r][c] = color
    return p


def _footprint(r, c):
    return {(r + dr, c + dc) for dr in range(3) for dc in range(3)}


def _select_seed_positions(rng, h, w, target):
    """Choose non-overlapping 3x3 seed footprints below row 3."""
    candidates = [(r, c) for r in range(4, h - 2) for c in range(0, w - 2)]
    rng.shuffle(candidates)
    best = []

    def rec(i, chosen, used):
        nonlocal best
        if len(chosen) > len(best):
            best = list(chosen)
        if len(chosen) >= target:
            return True
        if i >= len(candidates):
            return False
        if len(chosen) + (len(candidates) - i) <= len(best):
            return False
        for j in range(i, len(candidates)):
            r, c = candidates[j]
            fp = _footprint(r, c)
            if fp & used:
                continue
            if rec(j + 1, chosen + [(r, c)], used | fp):
                return True
        return False

    rec(0, [], set())
    return best[:target]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 7, 9)
        seed_bounds = (2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 11, 16)
        seed_bounds = (5, 8)
    else:
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 9, 13)
        seed_bounds = (3, 5)
    capacity = ((h - 4) // 3) * (w // 3)
    upper = min(seed_bounds[1], capacity)
    if upper < seed_bounds[0]:
        raise ValueError(
            f"grid {h}x{w} cannot fit the required {seed_bounds[0]} non-overlapping 3x3 seed footprints"
        )
    n_seeds = ctx.draw_int("n_seeds", seed_bounds[0], upper)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    proto2 = _make_proto(rng, 2)
    proto3 = _make_proto(rng, 3)
    # header rows 0-2: proto2 cols0-2, col3=9 separator, proto3 cols4-6
    for dr in range(3):
        for dc in range(3):
            g[dr][dc] = proto2[dr][dc]
            g[dr][4 + dc] = proto3[dr][dc]
        g[dr][3] = 9
    for c in range(w):           # row-3 full divider
        g[3][c] = 9
    # Seeds below the divider, 3x3 footprints non-overlapping.  Use exhaustive
    # candidate selection instead of random rejection so small easy boards do not
    # silently drop the required color-3 seed after placing only color 2.
    positions = _select_seed_positions(rng, h, w, n_seeds)
    if len(positions) != n_seeds:
        raise ValueError(
            f"grid {h}x{w} cannot place exact n_seeds={n_seeds} without overlapping 3x3 footprints"
        )
    colors = [2, 3] + [rng.choice([2, 3]) for _ in range(max(0, len(positions) - 2))]
    for (r, c), color in zip(positions, colors):
        g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 7
    g = full_grid(h, w, 0)
    # minimal header
    for dr in range(3):
        g[dr][0] = 2; g[dr][3] = 9; g[dr][4] = 3
    for c in range(w):
        g[3][c] = 9
    if name == "no_seeds":
        return g                      # header but no seeds -> nothing stamped
    if name == "single_seed":
        g[5][1] = 2                   # only one seed
        return g
    if name == "no_header":
        # seeds but no header prototypes -> nothing to stamp
        g2 = full_grid(h, w, 0)
        g2[5][1] = 2; g2[7][3] = 3
        return g2
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        errs.append("ragged grid")
        return errs
    if h < 7 or w < 7:
        errs.append("grid too small for header plus 3x3 stamps")
        return errs
    for r in range(3):
        if grid[r][3] != 9:
            errs.append("header separator col 3 is not all 9")
            break
    if any(grid[3][c] != 9 for c in range(w)):
        errs.append("row 3 is not a full divider")
    proto2 = [row[0:3] for row in grid[0:3]]
    proto3 = [row[4:7] for row in grid[0:3]]
    if not any(v == 2 for row in proto2 for v in row) or any(v not in {0, 2} for row in proto2 for v in row):
        errs.append("proto2 is not a 0/2 prototype")
    if not any(v == 3 for row in proto3 for v in row) or any(v not in {0, 3} for row in proto3 for v in row):
        errs.append("proto3 is not a 0/3 prototype")
    seeds = []
    for r in range(4, h):
        for c in range(w):
            if grid[r][c] in {2, 3}:
                seeds.append((r, c, grid[r][c]))
            elif grid[r][c] != 0:
                errs.append(f"unexpected nonzero value {grid[r][c]} below divider")
    if len(seeds) < 2:
        errs.append(f"expected at least two seeds, got {len(seeds)}")
    if {v for _, _, v in seeds} != {2, 3}:
        errs.append("seed area must include both colors 2 and 3")
    footprints = []
    for r, c, color in seeds:
        if r + 2 >= h or c + 2 >= w:
            errs.append(f"seed color {color} at {(r, c)} has out-of-bounds 3x3 stamp")
        fp = {(r + dr, c + dc) for dr in range(3) for dc in range(3)}
        for old in footprints:
            if fp & old:
                errs.append("seed 3x3 footprints overlap")
                return errs
        footprints.append(fp)
    return errs
