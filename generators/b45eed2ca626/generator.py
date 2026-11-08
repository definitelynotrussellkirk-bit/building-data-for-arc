"""Generator for ec883f72.

Rule: L-corner of one color casts a ray in the open diagonal
direction using the other color.

Combinatorial axes (8): grid_h/w, corner_orientation, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_corner, no_other, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b45eed2ca626"
VERSION = "3.0.1"  # SHAPE-LOCK poison fix: fixed 9x9 with a single center
# L-corner + other cell at fixed (8,8) -> 1 in/out shape. Rule finds ALL
# L-corners (e.g. every corner of a rectangular frame) and shoots each a
# diagonal ray of the other color outward. v3 builds a rectangular frame
# (4 corners all fire) + a small other-color marker inside, on varied grid
# sizes/positions.
TASK_ID = "b45eed2ca626"
SUMMARY = (
    "0-bg grid (h,w ~10-20) with a hollow RECTANGULAR FRAME (>=3x3) in an "
    "OUTER color and a small MARKER (1-4 cells) in a distinct OTHER color "
    "placed inside the frame's interior. The frame is positioned so its four "
    "corners have clear OUTWARD DIAGONALS. Rule: every L-corner of the outer "
    "color (a cell with exactly two orthogonal same-color neighbors forming an "
    "L bend) shoots a DIAGONAL RAY in the OTHER color outward (away from the "
    "frame) along the open diagonal, provided that diagonal is unobstructed."
)

INVARIANTS = [
    "background is color 0",
    "at least two nonzero colors are present",
    "one color forms an orthogonal L-corner",
    "outer and other colors are distinct and non-zero",
]

ORIENTATIONS = ("down_right", "down_left", "up_right", "up_left")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_corner", "no_other", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..16", "valid": "8..22"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "8..22"},
    "frame_h":        {"type": "int", "default": "rng 3..6", "valid": "3..9"},
    "frame_w":        {"type": "int", "default": "rng 3..6", "valid": "3..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "marker_size":    {"type": "int", "default": "rng 1..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "centered_frame",
                       "valid": "centered_frame"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(PALETTE_KINDS + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct non-bg colors (frame color + interior marker color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) != 2:
        errs.append(f"expected exactly 2 distinct non-bg colors; found {sorted(colors)}")
    return errs


def _poly(rng, k, max_h, max_w):
    cells = [(0, 0)]
    seen = {(0, 0)}
    tries = 0
    while len(cells) < k and tries < 120:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) in seen:
            continue
        cand = cells + [(nr, nc)]
        rs = [x for x, _ in cand]
        cs = [y for _, y in cand]
        if (max(rs) - min(rs) + 1 > max_h) or (max(cs) - min(cs) + 1 > max_w):
            continue
        cells.append((nr, nc))
        seen.add((nr, nc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        fh_hi, fw_hi = 4, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 14, 20)
        fh_hi, fw_hi = 7, 8
    else:
        h = ctx.draw_int("grid_h", 10, 16)
        w = ctx.draw_int("grid_w", 10, 16)
        fh_hi, fw_hi = 6, 6
    outer, other = ctx.draw_distinct_colors("colors", n=2, exclude={0})

    for _outer in range(80):
        g = full_grid(h, w, 0)
        fh = ctx.draw_int("frame_h", 3, min(fh_hi, h - 2))
        fw = ctx.draw_int("frame_w", 3, min(fw_hi, w - 2))
        # leave a >=1 margin so corners have an outward diagonal step
        r0 = rng.randint(1, h - fh - 1)
        c0 = rng.randint(1, w - fw - 1)
        # draw hollow rectangular frame
        for c in range(c0, c0 + fw):
            g[r0][c] = outer
            g[r0 + fh - 1][c] = outer
        for r in range(r0, r0 + fh):
            g[r][c0] = outer
            g[r][c0 + fw - 1] = outer
        # place an other-color marker strictly inside the frame interior
        interior = [(r, c) for r in range(r0 + 1, r0 + fh - 1)
                    for c in range(c0 + 1, c0 + fw - 1)]
        if not interior:
            continue
        msize = ctx.draw_int("marker_size", 1, 4)
        if len(interior) == 1:
            mr, mc = interior[0]
            g[mr][mc] = other
        else:
            ih = fh - 2
            iw = fw - 2
            shape = _poly(rng, min(msize, ih * iw), ih, iw)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            ar = rng.randint(r0 + 1, r0 + fh - 1 - sh)
            ac = rng.randint(c0 + 1, c0 + fw - 1 - sw)
            for dr, dc in shape:
                g[ar + dr][ac + dc] = other
        return g
    raise ValueError("could not realize frame layout")


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_corner":
        g[8][8] = 2
        return g
    if name == "no_other":
        g[4][4] = 1; g[4][5] = 1; g[5][4] = 1
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 1
        return g
    return g
