"""Generator for e681b708 — isolated dots adopt their room's marker colour.

REAL rule (verified from canonical Racket): background is 0. A lattice of
full color-1 rows/cols partitions the 0-bg into ROOMS (0-regions). MARKER cells
(any non-{0,1} colour) are embedded ON the lattice lines. Scattered ISOLATED
color-1 DOTS (a 1-cell with no cardinal 1-neighbour) sit inside the rooms. Each
dot is recoloured to the MAJORITY marker colour found in the 8-neighbourhood
border of the room it touches. Output size == input size.

The previous 2.0.0 body drew a gray (color-5) background with a single 0-room
and 2 fixed dots — an INVERTED distribution (canonical bg is 0, not 5) that
made the gray bg itself dominate every room's marker majority. This 3.0.0
rewrite builds the real structure: 0-bg, a color-1 line lattice with embedded
markers, and isolated 1-dots in the rooms.

Degenerates: no_rooms, no_dots, no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "65052ae2f657"
VERSION = "3.0.1"  # WRONG/inverted distribution: drew gray-5 bg single room (canonical bg is 0). Real rule: color-1 line lattice over 0-bg, markers on lines, isolated 1-dots in rooms -> each dot adopts its room's majority border-marker colour. Now build that structure with varied grid/lattice/markers/dots.
TASK_ID = "65052ae2f657"
SUMMARY = (
    "0-bg grid with a lattice of full COLOR-1 rows/cols dividing it into ROOMS. "
    "MARKER cells (non-{0,1} colours) are embedded on the lattice lines and at "
    "their endpoints. ISOLATED color-1 DOTS (no cardinal 1-neighbour) are "
    "scattered inside the rooms. Rule: recolour each dot to the MAJORITY marker "
    "colour in the 8-neighbour border of its room. Output size == input size."
)

INVARIANTS = [
    "background is 0",
    "a lattice of full color-1 lines partitions the bg into rooms",
    "marker cells (non-{0,1}) lie on the lattice lines",
    "isolated color-1 dots (no cardinal 1-neighbour) sit inside the rooms",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rooms", "no_dots", "no_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

_MARKERS = [2, 3, 4, 6, 7, 8, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 16..26", "valid": "11..28"},
    "grid_w":         {"type": "int", "default": "rng 16..26", "valid": "11..28"},
    "n_hlines":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_vlines":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_dots":         {"type": "int", "default": "rng", "valid": "3..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "line_lattice",
                       "valid": "line_lattice"},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "2..7"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 color-1 line cell; ≥1 non-{0,1} marker cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_1 = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    has_marker = any(grid[r][c] not in (0, 1) for r in range(h) for c in range(w))
    if not has_1:
        errs.append("no color-1 lattice line cells found")
    if not has_marker:
        errs.append("no non-{0,1} marker cells found")
    return errs


def _pick_lines(rng, n, lo, hi, gap):
    """n sorted positions in [lo,hi] spaced at least `gap` apart."""
    out = []
    for _ in range(200):
        if len(out) >= n:
            break
        p = rng.randint(lo, hi)
        if all(abs(p - q) >= gap for q in out):
            out.append(p)
    return sorted(out)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 14, 18)
        nh, nv, ndots = 1, 1, ctx.draw_int("n_dots", 3, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 22, 28); w = ctx.draw_int("grid_w", 22, 28)
        nh = ctx.draw_int("n_hlines", 2, 3); nv = ctx.draw_int("n_vlines", 2, 3)
        ndots = ctx.draw_int("n_dots", 7, 12)
    else:
        h = ctx.draw_int("grid_h", 16, 24); w = ctx.draw_int("grid_w", 16, 24)
        nh = ctx.draw_int("n_hlines", 1, 2); nv = ctx.draw_int("n_vlines", 1, 2)
        ndots = ctx.draw_int("n_dots", 4, 9)

    g = full_grid(h, w, 0)
    hrows = _pick_lines(rng, nh, 3, h - 4, 4)
    vcols = _pick_lines(rng, nv, 3, w - 4, 4)
    for r in hrows:
        for c in range(w):
            g[r][c] = 1
    for c in vcols:
        for r in range(h):
            g[r][c] = 1

    # markers embedded on the lines (and at endpoints), in 2-4 distinct colours
    mcolors = rng.sample(_MARKERS, rng.randint(2, 4))
    for r in hrows:
        g[r][0] = rng.choice(mcolors)
        g[r][w - 1] = rng.choice(mcolors)
        for _ in range(rng.randint(2, 4)):
            c = rng.randint(1, w - 2)
            if c not in vcols:
                g[r][c] = rng.choice(mcolors)
    for c in vcols:
        g[0][c] = rng.choice(mcolors)
        g[h - 1][c] = rng.choice(mcolors)
        for _ in range(rng.randint(2, 4)):
            r = rng.randint(1, h - 2)
            if r not in hrows:
                g[r][c] = rng.choice(mcolors)

    # scattered isolated color-1 dots inside rooms (no cardinal 1-neighbour,
    # >=1 cardinal 0-neighbour so a room is found)
    card = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    placed = 0
    for _ in range(ndots * 80):
        if placed >= ndots:
            break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if g[r][c] != 0:
            continue
        nb = [(r + dr, c + dc) for dr, dc in card]
        if any(g[nr][nc] == 1 for nr, nc in nb):
            continue
        if not any(g[nr][nc] == 0 for nr, nc in nb):
            continue
        g[r][c] = 1
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 16, 18
    g = full_grid(h, w, 0)
    for c in range(w):
        g[7][c] = 1
    if name == "no_rooms":
        # fill so there is no 0-region -> no room to anchor dots
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    if name == "no_markers":
        # lattice + dots but no markers -> dots have no majority (stay 1)
        g[2][3] = 1
        g[10][9] = 1
        return g
    if name == "no_dots":
        # lattice + markers but no isolated dots -> nothing recolours
        g[7][0] = 3; g[7][w - 1] = 3
        g[7][5] = 2
        return g
    return g
