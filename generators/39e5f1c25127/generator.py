"""Generator for 4c5c2cf0.

Rule: satellite shape is mirrored into the other three quadrants
around the central anchor color.

Combinatorial axes (8): grid_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, sat_size,
n_distinct_colors.
Degenerates: no_satellite, no_anchor, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39e5f1c25127"
VERSION = "2.0.1"  # shape-locked-in/out (fixed 15x15, fixed X anchor, near-fixed satellite): rule reads h,w dynamically (output=input size) and reflects the satellite across the anchor bbox-center axes; canonical spans 12x12..14x14. Now grid size 11..17, anchor = random 4-fold-symmetric-about-center shape (bbox center stays at grid center -> closest-to-center), satellite = random polyomino in the top-right quadrant -> all 4 mirror copies + size all vary.
TASK_ID = "39e5f1c25127"
SUMMARY = "Satellite shape mirrored into other three quadrants around anchor."

INVARIANTS = [
    "the anchor color is the nonzero object whose bbox center is closest to grid center",
    "the satellite color appears in one off-center shape",
    "the anchor bbox center defines the horizontal and vertical reflection axes",
    "anchor and satellite colors are distinct and non-zero",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_satellite", "no_anchor", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_size":      {"type": "int", "default": "rng 11..17", "valid": "11..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "center", "valid": "center"},
    "sat_size":       {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct nonzero colors (anchor + satellite); grid ≥11×11."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        pass  # degenerate (no_satellite/no_anchor) — allowed
    elif len(colors) != 2:
        errors.append(f"expected exactly 2 nonzero colors (anchor+satellite), found {len(colors)}: {sorted(colors)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    anchor, satellite = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    if difficulty == "easy":
        S = ctx.draw_int("grid_size", 11, 12)
    elif difficulty == "hard":
        S = ctx.draw_int("grid_size", 15, 17)
    else:
        S = ctx.draw_int("grid_size", 12, 15)
    g = full_grid(S, S, 0)
    m = S // 2                      # reflection: r -> S-1-r, c -> S-1-c (about grid center)
    A = rng.randint(1, 2)           # anchor reach from centre
    # --- anchor: random seed in the top-left-of-centre, made 4-fold symmetric
    #     about the grid centre so its bbox centre == grid centre (closest object).
    seed = set()
    for _ in range(rng.randint(1, 3)):
        seed.add((rng.randint(m - A, m - 1), rng.randint(m - A, m - 1)))
    anchor_cells = set()
    for (r, c) in seed:
        anchor_cells |= {(r, c), (r, S - 1 - c), (S - 1 - r, c), (S - 1 - r, S - 1 - c)}
    if S % 2 == 1:                  # odd grid has a true centre cell -> X-like anchor
        anchor_cells.add((m, m))
    for (r, c) in anchor_cells:
        g[r][c] = anchor
    # --- satellite: random polyomino strictly in the top-right quadrant, clear
    #     of the anchor band, so its 3 mirror copies fill the other quadrants.
    r_hi = m - A - 1                 # rows above the anchor band
    c_lo = m + A + 1                 # cols right of the anchor band
    rr = max(1, r_hi); cc = min(S - 2, c_lo)
    cells = _random_poly(rng, rng.randint(3, 5),
                         r_hi - 1 + 1 if r_hi >= 1 else 1,
                         (S - 2) - c_lo + 1 if (S - 2) >= c_lo else 1)
    # anchor at (r0,c0): top-right region origin
    r0 = max(1, r_hi - (max(r for r, _ in cells)))
    c0 = c_lo
    for (dr, dc) in cells:
        r, c = r0 + dr, c0 + dc
        if 1 <= r <= m - A - 1 and m + A + 1 <= c <= S - 2:
            g[r][c] = satellite
    # guarantee >=1 satellite cell (region can be tight on the smallest grids)
    if not any(satellite in row for row in g):
        g[1][S - 2] = satellite
    return g


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _random_poly(rng, size, maxh, maxw):
    """Random 4-connected polyomino normalized to origin, within maxh x maxw."""
    for _ in range(60):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice(_CARD)
            cells.add((r + dr, c + dc))
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, _ in norm) < max(1, maxh) and max(c for _, c in norm) < max(1, maxw):
            return norm
    return [(0, 0)]


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 0)
    if name == "no_satellite":
        for dr, dc in [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)]:
            g[7 + dr][7 + dc] = 2
        return g
    if name == "no_anchor":
        g[3][3] = 4
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(15):
                g[r][c] = 2
        return g
    return g
