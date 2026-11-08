"""Generator for arc_puzzle_bank_21_set22_s:S22_M2 — copy satellites between L-frames.

Rule (verified against canonical): there is a SOURCE frame — a color-2 cell with
a color-3 cell on one cardinal side and a color-4 cell on a PERPENDICULAR
cardinal side (an L-corner that defines a local coordinate basis: origin=the 2,
vx=direction to the 3, vy=direction to the 4). There is a TARGET frame of the
same shape in colors (5,6,7). Scattered around the source frame are SATELLITE
cells of color 8 and/or 9 (within Chebyshev radius 3 in the source's local
coords). The rule copies each satellite to the TARGET frame using the same local
coordinates — so the satellite constellation is re-placed around the target,
rotated/reflected to match the target frame's orientation.

This generator places a source L-frame + 8/9 satellites and a target L-frame
(independent orientation); the rule derives the output by copying the satellites
onto the target frame.

Combinatorial axes: grid_h, grid_w, source_orient, target_orient, n_satellites,
satellite_colors, positions.
Degenerates: no_pluses(no frames), single_plus(one frame), full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e562f7bff9ee"
VERSION = "2.0.0"  # WRONG-TASK rewrite. Docstring claimed '3-4 motifs, vertical pack' but the rule copies color-8/9 satellites from a (2,3,4) L-frame to a (5,6,7) L-frame using local frame coords. Old gen made separated single-color motifs -> NO multi-color L-corners could form, so find-frames had no valid frame; the rule ran on a degenerate empty frame and painted satellites at bogus positions (non-erroring garbage). Now builds the real source/target L-frames + satellites.
TASK_ID = "e562f7bff9ee"

SUMMARY = (
    "0-bg grid with a SOURCE L-frame (color-2 origin, color-3 along one cardinal "
    "axis vx, color-4 along a perpendicular axis vy), SATELLITE cells of color 8 "
    "and/or 9 scattered within Chebyshev radius 3 of the origin (in source-local "
    "coords), and a TARGET L-frame (color-5 origin, color-6 along vx', color-7 "
    "along vy') of independent orientation placed clear of the source. Rule: "
    "copy each satellite to the TARGET frame at the SAME local coordinates "
    "(so the constellation is re-placed around the target, rotated/reflected to "
    "the target's orientation). Source frame + satellites stay."
)

INVARIANTS = [
    "background is 0",
    "exactly one (2,3,4) source L-frame and one (5,6,7) target L-frame",
    "satellites are color 8/9 within Chebyshev radius 3 of the source origin (local)",
    "frames sit >=3 cells from every edge so copied satellites stay in bounds",
    "source and target regions are separated so satellites belong to one frame only",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pluses", "single_plus", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "10..24"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_satellites":   {"type": "int", "default": "rng 3..4", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_L_frames", "valid": "two_L_frames"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_pluses|single_plus|full_grid"},
}


def _perp_dirs(rng):
    """A cardinal vx and a perpendicular cardinal vy."""
    vx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    if vx[0] == 0:                 # vx horizontal -> vy vertical
        vy = rng.choice([(1, 0), (-1, 0)])
    else:                          # vx vertical -> vy horizontal
        vy = rng.choice([(0, 1), (0, -1)])
    return vx, vy


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 10, 12)
        n_sat = ctx.draw_int("n_satellites", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 16, 22)
        n_sat = ctx.draw_int("n_satellites", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        n_sat = ctx.draw_int("n_satellites", 3, 4)
    rng = ctx.draw_rng("layout")

    # local coords (chebyshev<=3) excluding origin and the two arm cells.
    locals_pool = [(u, v) for u in range(-3, 4) for v in range(-3, 4)
                   if max(abs(u), abs(v)) <= 3 and (u, v) not in ((0, 0), (1, 0), (0, 1))]

    def in_b(r, c):
        return 0 <= r < h and 0 <= c < w

    for _attempt in range(300):
        g = full_grid(h, w, 0)
        svx, svy = _perp_dirs(rng)
        tvx, tvy = _perp_dirs(rng)
        sor = rng.randint(3, h - 4); soc = rng.randint(3, w - 4)
        # target origin clear of edges and well-separated from source
        tor = toc = None
        for _ in range(80):
            r = rng.randint(3, h - 4); c = rng.randint(3, w - 4)
            if abs(r - sor) + abs(c - soc) >= 8:
                tor, toc = r, c
                break
        if tor is None:
            continue
        # paint frames
        g[sor][soc] = 2
        g[sor + svx[0]][soc + svx[1]] = 3
        g[sor + svy[0]][soc + svy[1]] = 4
        g[tor][toc] = 5
        g[tor + tvx[0]][toc + tvx[1]] = 6
        g[tor + tvy[0]][toc + tvy[1]] = 7

        chosen = rng.sample(locals_pool, min(n_sat, len(locals_pool)))
        placed = 0
        for (u, v) in chosen:
            wr = sor + u * svx[0] + v * svy[0]
            wc = soc + u * svx[1] + v * svy[1]
            tr = tor + u * tvx[0] + v * tvy[0]
            tc = toc + u * tvx[1] + v * tvy[1]
            if not (in_b(wr, wc) and in_b(tr, tc)):
                continue
            if g[wr][wc] != 0 or g[tr][tc] != 0:   # keep source clean + target landing on bg
                continue
            g[wr][wc] = rng.choice([8, 9])
            placed += 1
        if placed >= 1:
            return g
    # fallback minimal valid instance
    g = full_grid(12, 12, 0)
    g[3][3] = 2; g[3][4] = 3; g[4][3] = 4; g[2][4] = 8
    g[8][8] = 5; g[8][9] = 6; g[9][8] = 7
    return g


def _frame(grid, origin_color, x_color, y_color):
    """Return every L-frame as (origin, vx, vy): origin has x/y arms on
    perpendicular cardinal directions."""
    h, w = len(grid), len(grid[0])
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != origin_color:
                continue
            for vx in dirs:
                xr, xc = r + vx[0], c + vx[1]
                if not (0 <= xr < h and 0 <= xc < w and grid[xr][xc] == x_color):
                    continue
                for vy in dirs:
                    if vx[0] * vy[0] + vx[1] * vy[1] != 0:
                        continue
                    yr, yc = r + vy[0], c + vy[1]
                    if 0 <= yr < h and 0 <= yc < w and grid[yr][yc] == y_color:
                        out.append(((r, c), vx, vy))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the two oriented L-frames and source-local satellite contract."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    vals = [v for row in grid for v in row]
    if 0 not in vals:
        errs.append("no background cells")
    for color in (2, 3, 4, 5, 6, 7):
        if vals.count(color) != 1:
            errs.append(f"expected exactly one frame cell of color {color}; found {vals.count(color)}")
    sources = _frame(grid, 2, 3, 4)
    targets = _frame(grid, 5, 6, 7)
    if len(sources) != 1:
        errs.append(f"expected exactly one source (2,3,4) L-frame; found {len(sources)}")
    if len(targets) != 1:
        errs.append(f"expected exactly one target (5,6,7) L-frame; found {len(targets)}")
    if len(sources) != 1 or len(targets) != 1:
        return errs
    (sor, soc), svx, svy = sources[0]
    (tor, toc), tvx, tvy = targets[0]
    sat = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (8, 9)]
    if not sat:
        errs.append("no 8/9 source satellites")
    frame_local = {(0, 0), (1, 0), (0, 1)}
    visible_copies = 0
    for r, c in sat:
        dr, dc = r - sor, c - soc
        # Because svx/svy are perpendicular unit cardinal vectors, dot-products
        # recover source-local coordinates even when the frame is reflected.
        u = dr * svx[0] + dc * svx[1]
        v = dr * svy[0] + dc * svy[1]
        if max(abs(u), abs(v)) > 3:
            errs.append("satellite lies outside source-local Chebyshev radius 3")
            continue
        if (u, v) in frame_local:
            errs.append("satellite overlaps the source frame's local cells")
        tr = tor + u * tvx[0] + v * tvy[0]
        tc = toc + u * tvx[1] + v * tvy[1]
        if not (0 <= tr < h and 0 <= tc < w):
            errs.append("copied satellite would land out of bounds")
        elif grid[tr][tc] == 0:
            visible_copies += 1
    if sat and visible_copies == 0:
        errs.append("all copied satellites land on already-occupied cells; transformation is invisible")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_pluses":
        return g
    if name == "single_plus":
        g[5][5] = 2; g[5][6] = 3; g[6][5] = 4; g[4][6] = 8
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 3
        return g
    return g
