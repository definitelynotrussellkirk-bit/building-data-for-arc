"""Generator for 0962bcdd.

Rule: each cell that is a PLUS-center (interior, with all 4 cardinal
neighbors non-0) expands into a 5x5 starburst -- the length-2 cardinal
arms take the up-neighbor's color, and the length-2 diagonals plus the
center take the center cell's color.

This generator scatters isolated plus shapes (center + 4 arms) so each
center triggers one starburst; the 5x5 footprints are kept disjoint.

Combinatorial axes: grid size, plus count, the center/arm colors, and
positions.
Degenerates: no_centers, all_close, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "281f59ba6a02"
VERSION = "2.0.1"
TASK_ID = "281f59ba6a02"
SUMMARY = (
    "0-bg grid (size varies) with 1-N isolated PLUS shapes (a center cell + "
    "4 cardinal arm cells). Rule: each plus-center expands into a 5x5 "
    "starburst -- cardinal arms in the up-arm's color, diagonals+center in "
    "the center's color. The grid size, plus count, center/arm colors and "
    "positions vary freely (was a fixed setup, ~23 distinct)."
)

INVARIANTS = [
    "each plus is a center with 4 non-0 cardinal arms, isolated from others",
    "only the plus-centers have all 4 cardinal neighbors non-0",
    "the 5x5 starburst footprints are disjoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_centers", "all_close", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..24"},
    "n_plus":         {"type": "int", "default": "varies", "valid": "1..5"},
    "center_color":   {"type": "color", "default": "rng !0", "valid": "1..9"},
    "arm_color":      {"type": "color", "default": "rng !0", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_centers|all_close|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one plus-center (interior cell with 4 non-zero cardinal neighbors)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_centers", "all_close", "full_grid"):
        return []
    errs = []
    # Check at least one plus-center: interior cell with all 4 cardinal neighbors non-zero
    found = False
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if (grid[r][c] != 0 and
                    grid[r-1][c] != 0 and grid[r+1][c] != 0 and
                    grid[r][c-1] != 0 and grid[r][c+1] != 0):
                found = True
                break
        if found:
            break
    if not found:
        errs.append("no plus-center found (cell with 4 non-zero cardinal neighbors)")
    return errs


def _reserve(occ, top, left, sz, h, w, margin=1):
    for r in range(top - margin, top + sz + margin):
        for c in range(left - margin, left + sz + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sz):
        for c in range(left, left + sz):
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
        hr, wr, nr = (10, 13), (10, 14), (1, 2)
    elif difficulty == "hard":
        hr, wr, nr = (16, 22), (18, 24), (3, 5)
    else:
        hr, wr, nr = (12, 17), (13, 19), (2, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        for _ in range(rng.randint(*nr)):
            for _t in range(30):
                # center at (cr,cc) so the 5x5 starburst (cr-2..cr+2) fits
                cr = rng.randint(2, h - 3); cc = rng.randint(2, w - 3)
                # reserve the 5x5 footprint (top-left cr-2,cc-2) + margin
                if _reserve(occ, cr - 2, cc - 2, 5, h, w):
                    a = rng.randint(1, 9)
                    b = rng.choice([x for x in range(1, 10) if x != a])
                    g[cr][cc] = a
                    g[cr - 1][cc] = b        # up-arm = arm color
                    g[cr + 1][cc] = b
                    g[cr][cc - 1] = b
                    g[cr][cc + 1] = b
                    placed += 1
                    break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    g[4][4] = 3; g[3][4] = 6; g[5][4] = 6; g[4][3] = 6; g[4][5] = 6
    if name == "no_centers":
        return full_grid(9, 9, 0)
    if name == "all_close":
        g[2][2] = 3; g[1][2] = 6; g[3][2] = 6; g[2][1] = 6; g[2][3] = 6
        return g
    if name == "full_grid":
        return full_grid(9, 9, 4)
    return g
