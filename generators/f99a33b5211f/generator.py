"""Generator for arc_puzzle_bank_21_set22_s:S22_E3.

Rule: a target marker frame defines a local three-cell x-axis bar.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frame, full_grid, blank.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.local_frame import choose_frame, draw_marker_frame

GENERATOR_ID = "f99a33b5211f"
VERSION = "3.1.0"  # bigger grids + non-5/6/7 distractor objects (rule ignores them) -> more shapes/colors; single frame kept unambiguous
TASK_ID = "f99a33b5211f"
SUMMARY = (
    "0-bg grid (h, w~7-10) "
    "with ONE TARGET "
    "MARKER FRAME — a "
    "3-cell L-shape "
    "anchored at a chosen "
    "origin (orig, vx, vy)"
    " painted in 3 marker "
    "colors {5, 6, 7} "
    "(per helpers/local_"
    "frame). The frame "
    "establishes a LOCAL "
    "COORDINATE SYSTEM "
    "where (2, 0) (2 cells "
    "along the x-axis "
    "from the origin) is "
    "IN-BOUNDS and INITIALLY"
    " BLANK. Rule (DRAW A "
    "3-CELL X-AXIS BAR IN "
    "THE LOCAL FRAME): "
    "interpret the marker "
    "frame's 3 cells as "
    "(origin, x-direction "
    "vector, y-direction "
    "vector). Compute the "
    "LOCAL COORDINATE (2, "
    "0) — i.e., origin + "
    "2*vx + 0*vy. PAINT "
    "cells at LOCAL (0, "
    "0), (1, 0), (2, 0) "
    "(a 3-cell run along "
    "the local x-axis "
    "starting from origin)"
    " with the FRAME's "
    "color or a specific "
    "color per puzzle "
    "convention. Net: the "
    "marker frame extends "
    "into a 3-cell bar "
    "in its declared "
    "x-direction."
)

INVARIANTS = [
    "background is 0",
    "there is exactly one target frame with colors 5,6,7",
    "local coordinate (2,0) is in bounds and blank",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "full_grid", "blank")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-11 easy / 10-15 med / 13-20 hard", "valid": "7..22"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 10-15 med / 13-20 hard", "valid": "7..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "n_distractor":   {"type": "int", "default": "0-1 easy / 1-3 med / 2-4 hard (non-5/6/7)", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "3 frame + distractors", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "up to 8", "valid": "3..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_frame|full_grid|blank"},
}

_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _rand_blob(rng, size):
    cells = {(0, 0)}; frontier = [(0, 0)]
    while len(cells) < size and frontier:
        cr, cc = rng.choice(frontier)
        opts = [(cr + dr, cc + dc) for dr, dc in _CARD if (cr + dr, cc + dc) not in cells]
        if not opts:
            frontier.remove((cr, cc)); continue
        nc = rng.choice(opts); cells.add(nc); frontier.append(nc)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _place_distractor(grid, occ, cells, color, rng):
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
    for _ in range(60):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        ok = True
        for dr, dc in cells:
            r, c = r0 + dr, c0 + dc
            for hr in range(r - 1, r + 2):
                for hc in range(c - 1, c + 2):
                    if 0 <= hr < h and 0 <= hc < w and occ[hr][hc]:
                        ok = False; break
                if not ok: break
            if not ok: break
        if ok:
            for dr, dc in cells:
                grid[r0 + dr][c0 + dc] = color
                occ[r0 + dr][c0 + dc] = True
            return True
    return False


def _target_frames(grid):
    """Return unambiguous 5(origin), 6(x), 7(y) local frames in ``grid``."""
    h, w = len(grid), len(grid[0])
    frames = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5:
                continue
            for vx in _CARD:
                xr, xc = r + vx[0], c + vx[1]
                if not (0 <= xr < h and 0 <= xc < w) or grid[xr][xc] != 6:
                    continue
                for vy in _CARD:
                    if vx[0] * vy[0] + vx[1] * vy[1] != 0:
                        continue
                    yr, yc = r + vy[0], c + vy[1]
                    if 0 <= yr < h and 0 <= yc < w and grid[yr][yc] == 7:
                        frames.append(((r, c), vx, vy))
    return frames


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the generated input has one usable local frame and a blank tip."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    if any(v == 8 for row in grid for v in row):
        errs.append("input already contains output color 8")
    frames = _target_frames(grid)
    if len(frames) != 1:
        errs.append(f"expected exactly one 5/6/7 local frame, found {len(frames)}")
        return errs
    (orow, ocol), vx, _vy = frames[0]
    tr, tc = orow + 2 * vx[0], ocol + 2 * vx[1]
    h = len(grid)
    if not (0 <= tr < h and 0 <= tc < w):
        errs.append("local coordinate (2,0) is out of bounds")
    elif grid[tr][tc] != 0:
        errs.append("local coordinate (2,0) is not blank")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 8, 11); ndr = (0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 20); w = ctx.draw_int("grid_w", 13, 20); ndr = (2, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 15); w = ctx.draw_int("grid_w", 10, 15); ndr = (1, 3)
    grid = full_grid(h, w, 0)
    origin, vx, vy = choose_frame(rng, h, w, [(2, 0)])
    draw_marker_frame(grid, origin, vx, vy, (5, 6, 7))

    # reserve frame cells + the painted bar target (2,0) + halo, then scatter
    # distractor objects in non-{5,6,7} colors (the rule never matches them, so
    # they pass through untouched -> input diversity, single frame stays unique).
    occ = [[False] * w for _ in range(h)]
    pts = [origin,
           (origin[0] + vx[0], origin[1] + vx[1]),
           (origin[0] + vy[0], origin[1] + vy[1]),
           (origin[0] + 2 * vx[0], origin[1] + 2 * vx[1])]
    for (pr, pc) in pts:
        for hr in range(pr - 1, pr + 2):
            for hc in range(pc - 1, pc + 2):
                if 0 <= hr < h and 0 <= hc < w:
                    occ[hr][hc] = True
    dcols = [1, 2, 3, 4, 9]
    rng.shuffle(dcols)
    for i in range(rng.randint(*ndr)):
        _place_distractor(grid, occ, _rand_blob(rng, rng.randint(2, 5)),
                          dcols[i % len(dcols)], rng)
    return grid


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "no_frame":
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 5
        return g
    if name == "blank":
        return g
    return g
