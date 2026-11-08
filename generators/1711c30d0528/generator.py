"""Generator for arc_additional_puzzle_bank_volume4:H27.

Rule: 5-color rectangular frames create nesting depth (a frame contains an
object when the object's cells all sit strictly inside the frame's bbox).
Pick the non-5 object with max depth; ties broken by largest size. Output is
the bbox-cropped mask of that object (painted its own color, bg 0).

Combinatorial axes (8): grid_h, grid_w, palette_kind, outer_frame_size,
inner_frame_size, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_frames, single_frame, both_blobs_at_same_depth.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid, paint_at

GENERATOR_ID = "1711c30d0528"
# 2.1.0: output = cropped inner blob, drawn from a small 8-shape bank
#        (dup-outputs 29%). Expanded inner-shape bank with more 3-5 cell
#        shapes that fit a 3x3 interior, and grow the inner frame more often
#        to 4-5 so larger blobs fit -> more distinct output crops.
VERSION = "2.2.0"
TASK_ID = "1711c30d0528"
SUMMARY = (
    "0-bg grid (h~11-18, w~11-18) with TWO NESTED "
    "COLOR-5 RECTANGULAR FRAMES (concentric): "
    "(a) OUTER FRAME — hollow rectangle of size "
    "oh × ow (7..12 each), placed at random interior "
    "position, painted entirely in COLOR 5 (border-"
    "only); (b) INNER FRAME — hollow rectangle of "
    "size ih × iw (3..5 each), nested STRICTLY "
    "INSIDE the outer frame with at least 1-cell "
    "gap on all sides, also painted in COLOR 5. "
    "Inside the inner frame's interior: (c) INNER "
    "BLOB — a small shape (1-4 cells) drawn from "
    "_INNER_SHAPES bank, painted in INNER_COLOR "
    "(non-5 distinct color). Outside the outer "
    "frame: (d) OUTER BLOB — a small shape (1-4 "
    "cells) drawn from _OUTER_SHAPES bank, painted "
    "in OUTER_COLOR (non-5 distinct color). The "
    "INNER blob has NESTING DEPTH 2 (inside 2 "
    "frames); the OUTER blob has NESTING DEPTH 0 "
    "(outside all frames). Rule (PICK THE MAX-DEPTH "
    "NON-5 BLOB, OUTPUT ITS BBOX-CROPPED MASK IN "
    "ITS OWN COLOR): for EACH non-5 blob in the "
    "input, COMPUTE its NESTING DEPTH = number of "
    "rectangular 5-FRAMES whose bbox strictly "
    "contains every cell of the blob. SELECT the "
    "blob with MAXIMUM DEPTH (ties broken by "
    "largest size). CROP it to its bbox. OUTPUT the "
    "crop with the blob's color preserved, bg 0. "
    "All frames and other blobs are discarded. "
    "Net: only the most-deeply-nested colored blob "
    "survives, output as a small cropped grid. "
    "Flagged intrinsic-low (uniq_out=23): output "
    "drawn from small _INNER_SHAPES × color bank."
)

# Rivals: 'output the outer blob' refuted by ≥2 demos where the outer
# blob has a different shape/color than the deepest one (output picks
# inner). 'output is the inner frame' refuted by any demo (output is a
# small blob, not a frame). 'count cells regardless of depth' refuted
# by ≥1 demo where the outer blob is larger but shallower (depth
# beats size). 4 demos with varied blob shapes + frame sizes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly 2 nested 5-frames",
    "exactly one non-5 blob inside both frames (depth 2)",
    "exactly one non-5 blob outside (depth 0)",
]

PALETTE_KINDS = ("default", "wide_outer", "tall_outer", "balanced")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "both_blobs_at_same_depth")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "2", "valid": "2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "concentric_random",
                       "valid": "concentric_random"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_INNER_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0)],
    [(0, 0), (1, 1)],
    # extra shapes (3-5 cells) that fit a 3x3 interior
    [(0, 1), (1, 0), (1, 1), (1, 2)],          # T (4)
    [(0, 0), (1, 0), (2, 0)],                   # I3 vertical
    [(0, 0), (0, 1), (0, 2)],                   # I3 horizontal
    [(0, 0), (1, 0), (1, 1), (2, 1)],          # S (4)
    [(0, 1), (1, 0), (1, 1), (2, 1)],          # T-rot (4)
    [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],  # X (5)
    [(0, 0), (1, 0), (2, 0), (2, 1)],          # L (4)
    [(0, 0), (0, 1), (0, 2), (1, 1)],          # T2 (4)
]

_OUTER_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0)],
]


def _is_4_connected(shape):
    cells = set(shape)
    stack = [next(iter(cells))]
    seen = {stack[0]}
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (r + dr, c + dc)
            if p in cells and p not in seen:
                seen.add(p)
                stack.append(p)
    return len(seen) == len(cells)


# The canonical rule uses 4-connected `objects`.  Two legacy bank shapes were
# diagonal-only / X-like supports, so one intended inner blob became multiple
# deepest objects with identical depth.  Filter the pedagogical shape banks to
# connected supports only; disconnected degenerates belong in opt-in textures,
# not the default stream.
_INNER_SHAPES = [s for s in _INNER_SHAPES if _is_4_connected(s)]
_OUTER_SHAPES = [s for s in _OUTER_SHAPES if _is_4_connected(s)]


def _shape_fits(g, r0, c0, shape):
    h, w = len(g), len(g[0])
    for dr, dc in shape:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < h and 0 <= c < w): return False
        if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
        outer_sz_lo, outer_sz_hi = 7, 7
        inner_sz_lo, inner_sz_hi = 3, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        outer_sz_lo, outer_sz_hi = 9, 12
        inner_sz_lo, inner_sz_hi = 4, 5
    else:
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 13, 16)
        outer_sz_lo, outer_sz_hi = 8, 11
        inner_sz_lo, inner_sz_hi = 4, 5
    inner_color, outer_color = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)
    for _ in range(60):
        g = full_grid(h, w, 0)
        oh = rng.randint(outer_sz_lo, outer_sz_hi)
        ow = rng.randint(outer_sz_lo, outer_sz_hi)
        oh = min(oh, h - 2); ow = min(ow, w - 2)
        or0 = rng.randint(1, h - oh - 1)
        oc0 = rng.randint(1, w - ow - 1)
        or1 = or0 + oh - 1
        oc1 = oc0 + ow - 1
        ih = rng.randint(inner_sz_lo, inner_sz_hi)
        iw = rng.randint(inner_sz_lo, inner_sz_hi)
        ih = min(ih, oh - 4); iw = min(iw, ow - 4)
        if ih < 3 or iw < 3: continue
        ir0 = or0 + rng.randint(2, oh - ih - 2)
        ic0 = oc0 + rng.randint(2, ow - iw - 2)
        ir1 = ir0 + ih - 1
        ic1 = ic0 + iw - 1
        draw_frame(g, or0, oc0, or1, oc1, 5)
        draw_frame(g, ir0, ic0, ir1, ic1, 5)
        # Place inner blob STRICTLY inside the inner frame
        inner_shape = rng.choice(_INNER_SHAPES)
        sh = max(r for r, _ in inner_shape) + 1
        sw = max(c for _, c in inner_shape) + 1
        if sh > ih - 2 or sw > iw - 2: continue
        # interior of inner frame is (ir0+1..ir1-1, ic0+1..ic1-1)
        i_r0 = rng.randint(ir0 + 1, ir1 - 1 - sh + 1)
        i_c0 = rng.randint(ic0 + 1, ic1 - 1 - sw + 1)
        if not _shape_fits(g, i_r0, i_c0, inner_shape): continue
        paint_at(g, i_r0, i_c0, inner_shape, inner_color)
        # Place outer blob OUTSIDE the outer frame
        outer_shape = rng.choice(_OUTER_SHAPES)
        osh = max(r for r, _ in outer_shape) + 1
        osw = max(c for _, c in outer_shape) + 1
        placed = False
        for _ in range(120):
            o_r0 = rng.randint(0, h - osh)
            o_c0 = rng.randint(0, w - osw)
            # All cells must be outside outer frame's bbox
            outside = True
            for dr, dc in outer_shape:
                r2, c2 = o_r0 + dr, o_c0 + dc
                if or0 <= r2 <= or1 and oc0 <= c2 <= oc1:
                    outside = False; break
            if not outside: continue
            if not _shape_fits(g, o_r0, o_c0, outer_shape): continue
            paint_at(g, o_r0, o_c0, outer_shape, outer_color)
            placed = True; break
        if placed: return g
    # Fallback to legacy layout
    g = full_grid(h, w, 0)
    draw_frame(g, 2, 2, 8, 8, 5)
    draw_frame(g, 4, 4, 6, 6, 5)
    g[5][5] = inner_color
    g[0][0] = outer_color
    return g


def _draw_from_degenerate(name, rng):
    from puzzle_generators.helpers.shape import L_TROMINO_NE, L_TROMINO_SE
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_frames":
        paint_at(g, 5, 5, L_TROMINO_NE, 3)
        paint_at(g, 0, 0, L_TROMINO_SE, 1)
        return g
    if name == "single_frame":
        draw_frame(g, 2, 2, 8, 8, 5)
        paint_at(g, 5, 5, L_TROMINO_NE, 3)
        paint_at(g, 0, 0, L_TROMINO_SE, 1)
        return g
    if name == "both_blobs_at_same_depth":
        draw_frame(g, 2, 2, 8, 8, 5)
        draw_frame(g, 4, 4, 6, 6, 5)
        paint_at(g, 5, 5, L_TROMINO_NE, 3)
        paint_at(g, 7, 7, L_TROMINO_SE, 1)
        return g
    return g


def _components(grid, color=None):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (color is not None and grid[r][c] != color) or (r, c) in seen:
                continue
            col = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == col
                            and (color is None or grid[nr][nc] == color)):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            comps.append({"color": col, "cells": cells,
                          "bbox": (min(rs), min(cs), max(rs), max(cs))})
    return comps


def _is_frame(comp):
    if comp["color"] != 5:
        return False
    r1, c1, r2, c2 = comp["bbox"]
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return False
    want = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)}
    return set(comp["cells"]) == want


def _depth(obj, frames):
    d = 0
    for fr in frames:
        r1, c1, r2, c2 = fr["bbox"]
        if all(r1 < r < r2 and c1 < c < c2 for r, c in obj["cells"]):
            d += 1
    return d


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    frames = [c for c in _components(grid, 5) if _is_frame(c)]
    if len(frames) != 2:
        errs.append(f"expected exactly two connected color-5 frames, got {len(frames)}")
    objs = [c for c in _components(grid) if c["color"] != 5]
    if len(objs) < 2:
        errs.append(f"expected at least two non-frame objects, got {len(objs)}")
    if len(frames) == 2 and objs:
        depths = [_depth(o, frames) for o in objs]
        if depths.count(2) != 1:
            errs.append(f"expected exactly one object at depth 2, got depths={depths}")
        if 0 not in depths:
            errs.append(f"missing outside depth-0 distractor, got depths={depths}")
    return errs
