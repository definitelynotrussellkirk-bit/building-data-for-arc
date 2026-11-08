"""Generator for arc_additional_puzzles_21_set8:H53 — rank+transform a candidate, center in frame.

Rule: rank candidate components by area, transform the requested one,
and center it in a frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rank,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rank, no_frame, no_candidates.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "182d3949bec6"
# 1.2.0: was a fully fixed 12x16 grid with a fixed 8x6 frame and 3 fixed
#        shapes (shape-locked in & out, dup-outputs). Now randomize grid
#        size, frame size/position, and grow distinct-area random
#        polyominoes for candidates; output (frame interior) shape now varies.
VERSION = "1.2.1"
TASK_ID = "182d3949bec6"
SUMMARY = "Rank candidate components by area, transform the requested one, and center it in a frame."

INVARIANTS = [
    "cell (0,0) gives a one-based area rank",
    "the last cell of row 0 gives the transform command",
    "one color-8 rectangular frame is the destination",
    "candidate components have distinct areas and all transforms fit inside the frame interior",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rank", "no_frame", "no_candidates")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12..12"},
    "grid_w":         {"type": "int", "default": "16", "valid": "16..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rank":           {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "transform":      {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "rank_transform_with_frame",
                       "valid": "rank_transform_with_frame"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2), (3, 1)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: cell (0,0) is the rank (nonzero), color-8 frame cells present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_rank", "no_frame", "no_candidates"):
        return errs
    if grid[0][0] == 0:
        errs.append("cell (0,0) should be the area-rank command (non-zero)")
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not eights:
        errs.append("no color-8 frame cells found")
    return errs


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _grow_poly(rng, size, max_h, max_w, attempts=40):
    """Grow a connected polyomino of `size` cells fitting in max_h x max_w.
    Returns normalized cell list (min r/c = 0) or None."""
    for _ in range(attempts):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) in seen:
                continue
            cand = cells + [(nr, nc)]
            rs = [x for x, _ in cand]
            cs = [y for _, y in cand]
            if (max(rs) - min(rs) + 1) > max_h or (max(cs) - min(cs) + 1) > max_w:
                continue
            cells.append((nr, nc))
            seen.add((nr, nc))
        rs = [x for x, _ in cells]
        cs = [y for _, y in cells]
        mr, mc = min(rs), min(cs)
        return sorted((r - mr, c - mc) for r, c in cells)
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        transform = ctx.draw_int("transform", 1, 1)
        n_cand = 3
    elif difficulty == "hard":
        transform = ctx.draw_int("transform", 2, 4)
        n_cand = rng.randint(3, 4)
    else:
        transform = ctx.draw_int("transform", 1, 4)
        n_cand = rng.randint(3, 4)

    # Build n_cand candidate polyominoes with DISTINCT areas (so the
    # area-then-color sort and rank command are unambiguous).
    sizes = rng.sample([3, 4, 5, 6, 7], n_cand)
    max_obj = max(sizes)
    # Frame interior must fit the largest candidate under any of the 4
    # transforms; a square interior of side >= max_obj is always safe.
    interior = max_obj + rng.randint(1, 3)          # frame interior side
    fh = interior + 2                                 # frame outer height
    fw = interior + rng.randint(0, 2) + 2            # frame outer width (>=interior)
    finner = fw - 2

    # Grid: a left "candidate column" region + the frame on the right.
    cand_w = 8
    # Need h - fh - 1 >= 2 so the frame-row placement randint(2, h-fh-1) below is
    # a non-empty range; fh+2 left only one legal row (randint(2,1) -> crash).
    h = max(fh + 3, 12) + rng.randint(0, 3)
    w = cand_w + fw + 2 + rng.randint(0, 2)

    g = full_grid(h, w, 0)
    # Frame placement on the right side.
    fr = rng.randint(2, h - fh - 1)
    fc = w - fw - 1
    draw_frame(g, fr, fc, fr + fh - 1, fc + fw - 1, 8)

    # Place candidates in the left column region, vertically stacked,
    # non-touching, in distinct colors.
    colors = rng.sample([2, 3, 4, 5, 6, 7, 9], n_cand)
    cur_r = 1
    placed = 0
    region_w = cand_w - 1
    for size, color in zip(sizes, colors):
        poly = _grow_poly(rng, size, 4, region_w)
        if poly is None:
            continue
        ph = max(r for r, _ in poly) + 1
        pw = max(c for _, c in poly) + 1
        if cur_r + ph > h - 1:
            break
        c0 = rng.randint(1, max(1, region_w - pw))
        _paint(g, cur_r, c0, poly, color)
        cur_r += ph + 1            # 1-row gap keeps components separate
        placed += 1

    # rank command: pick a valid 1-based rank within placed candidates.
    rank_hi = max(1, placed)
    rank = ctx.draw_int("rank", 1, rank_hi)
    g[0][0] = rank
    g[0][w - 1] = transform
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 16, 0)
    if name == "no_rank":
        # frame + candidates + transform but (0,0) is bg → no rank to apply
        g[0][15] = 2
        draw_frame(g, 3, 9, 10, 14, 8)
        _paint(g, 2, 1, _SHAPES[0], 4)
        _paint(g, 5, 1, _SHAPES[1], 6)
        _paint(g, 7, 5, _SHAPES[2], 7)
        return g
    if name == "no_frame":
        # rank + transform + candidates but no 8-frame → nowhere to center stamp
        g[0][0] = 2
        g[0][15] = 3
        _paint(g, 2, 1, _SHAPES[0], 4)
        _paint(g, 5, 1, _SHAPES[1], 6)
        _paint(g, 7, 5, _SHAPES[2], 7)
        return g
    if name == "no_candidates":
        # rank + transform + frame but no body candidates → no shape to pick
        g[0][0] = 2
        g[0][15] = 3
        draw_frame(g, 3, 9, 10, 14, 8)
        return g
    return g
