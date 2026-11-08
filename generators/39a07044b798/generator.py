"""Generator for 39a07044b798 — fit left-side inserts into right-side frames.

Rule: the left half contains detached inserts; the right half contains hollow
frames.  Match each insert to the frame whose interior dimensions fit it
(allowing a 90° rotation), then emit the right half with the insert pasted
inside its matching frame.

Degenerates: no_frames, no_inserts, tied_sizes.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "39a07044b798"
VERSION = "2.0.0"  # was a wrong-task multi-motif gallery generator; canonical is split-canvas frame insertion.
TASK_ID = "39a07044b798"

SUMMARY = (
    "Even-width split canvas: left half has detached colored inserts; right half "
    "has hollow frames with distinct interior dimensions. Each insert bbox matches "
    "exactly one frame interior, sometimes only after 90° rotation."
)

INVARIANTS = [
    "input width is even; output is the right half",
    "left half contains one detached insert per right-half frame",
    "right half contains 2-3 hollow rectangular frames",
    "frame interior dimensions are unique up to 90° rotation",
    "at least one insert requires rotation to fit its frame",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_inserts", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "grid_w_half":    {"type": "int", "default": "rng 11..15", "valid": "8..15"},
    "n":              {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "split_canvas_frames_inserts",
                       "valid": "split_canvas_frames_inserts"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _shape_cells(ih, iw):
    """Connected, bbox-exact, rotation-visible insert shape."""
    cells = {(r, c) for r in range(ih) for c in range(iw)}
    # Remove a corner and, when possible, one adjacent edge cell.  The remaining
    # shape is connected, has the requested bbox, and makes a 90° rotation visible.
    cells.discard((0, iw - 1))
    if ih >= 3 and iw >= 3:
        cells.discard((1, iw - 1))
    return sorted(cells)


def _place_rect(g, rh, rw, rng, *, c_lo, c_hi):
    h, _w = len(g), len(g[0])
    if rh > h or rw > (c_hi - c_lo):
        return None
    for _ in range(240):
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(c_lo, c_hi - rw)
        if _free(g, r0, c0, r0 + rh - 1, c0 + rw - 1):
            return r0, c0
    return None


def _deterministic_fallback():
    h, half = 14, 14
    g = full_grid(h, half * 2, 0)
    # (insert_h, insert_w, frame_interior_h, frame_interior_w, color, frame_color)
    specs = [
        (2, 3, 3, 2, 2, 7),   # requires rotation
        (3, 4, 3, 4, 3, 8),
        (2, 5, 2, 5, 4, 5),
    ]
    insert_pos = [(1, 1), (6, 1), (10, 1)]
    frame_pos = [(1, half + 1), (1, half + 7), (8, half + 1)]
    for (sh, sw, ih, iw, color, fcol), (ir, ic), (fr, fc) in zip(specs, insert_pos, frame_pos):
        _paint(g, ir, ic, _shape_cells(sh, sw), color)
        draw_frame(g, fr, fc, fr + ih + 1, fc + iw + 1, fcol)
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        half = ctx.draw_int("grid_w_half", 11, 13)
        n = ctx.draw_int("n", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 15)
        half = ctx.draw_int("grid_w_half", 13, 15)
        n = ctx.draw_int("n", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        half = ctx.draw_int("grid_w_half", 12, 15)
        n = ctx.draw_int("n", 2, 3)
    rng = ctx.draw_rng("layout")

    # Unique under rotation, so the canonical first-candidate matcher has a
    # single intended insert for every frame.
    dim_pool = [(2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (4, 5)]
    rng.shuffle(dim_pool)
    insert_dims = dim_pool[:n]
    insert_colors = rng.sample([1, 2, 3, 4, 6, 9], n)
    frame_colors = rng.sample([5, 7, 8], min(n, 3))
    if len(frame_colors) < n:
        frame_colors += rng.sample([1, 2, 3, 4, 6, 9], n - len(frame_colors))

    # Force one rotation-visible case per default instance; rotate some others.
    rotate_flags = [True] + [rng.random() < 0.45 for _ in range(n - 1)]

    for _outer in range(60):
        g = full_grid(h, half * 2, 0)
        ok = True
        specs = []
        for (sh, sw), color, fcol, rot in zip(insert_dims, insert_colors, frame_colors, rotate_flags):
            ih, iw = (sw, sh) if rot else (sh, sw)
            specs.append((sh, sw, ih, iw, color, fcol))
        rng.shuffle(specs)
        for sh, sw, ih, iw, color, fcol in specs:
            ipos = _place_rect(g, sh, sw, rng, c_lo=0, c_hi=half)
            fpos = _place_rect(g, ih + 2, iw + 2, rng, c_lo=half, c_hi=half * 2)
            if ipos is None or fpos is None:
                ok = False
                break
            _paint(g, ipos[0], ipos[1], _shape_cells(sh, sw), color)
            draw_frame(g, fpos[0], fpos[1], fpos[0] + ih + 1, fpos[1] + iw + 1, fcol)
        if ok:
            return g
    return _deterministic_fallback()


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 20, 0)
    mid = 10
    if name == "no_frames":
        _paint(g, 2, 1, _shape_cells(2, 3), 2)
        _paint(g, 6, 1, _shape_cells(3, 2), 3)
        return g
    if name == "no_inserts":
        draw_frame(g, 1, mid + 1, 4, mid + 5, 7)
        draw_frame(g, 5, mid + 1, 9, mid + 4, 8)
        return g
    if name == "tied_sizes":
        _paint(g, 2, 1, _shape_cells(2, 3), 2)
        _paint(g, 6, 1, _shape_cells(3, 2), 3)
        draw_frame(g, 1, mid + 1, 4, mid + 5, 7)  # interior 2x3
        draw_frame(g, 5, mid + 1, 9, mid + 4, 8)  # interior 3x2; same up to rotation
        return g
    return _deterministic_fallback()


# ----------------------------- self_check support -------------------------

def _components(g, *, col_offset=0):
    h, w = len(g), len(g[0]) if g else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)]); seen.add((r, c)); cells = []
            color = g[r][c]
            while q:
                rr, cc = q.popleft(); cells.append((rr, cc + col_offset))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and g[nr][nc] != 0:
                        seen.add((nr, nc)); q.append((nr, nc))
            comps.append({"color": color, "cells": cells})
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_frame(comp):
    cells = set(comp["cells"])
    r1, c1, r2, c2 = _bbox(cells)
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return False
    outline = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
               if r in (r1, r2) or c in (c1, c2)}
    return cells == outline


def _dims(comp):
    r1, c1, r2, c2 = _bbox(comp["cells"])
    return r2 - r1 + 1, c2 - c1 + 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    msgs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if w % 2:
        msgs.append("input width is odd; canonical split would be ambiguous")
    mid = w // 2
    left = [row[:mid] for row in grid]
    right = [row[mid:] for row in grid]
    inserts = _components(left)
    frames = [c for c in _components(right, col_offset=mid) if _is_frame(c)]
    if len(inserts) < 2:
        msgs.append("fewer than two left-half inserts")
    if len(frames) < 2:
        msgs.append("fewer than two right-half frames")
    frame_interiors = []
    for fr in frames:
        fh, fw = _dims(fr)
        frame_interiors.append((fh - 2, fw - 2))
    if len({tuple(sorted(d)) for d in frame_interiors}) != len(frame_interiors):
        msgs.append("frame interior dimensions are not unique up to rotation")
    insert_dims = [_dims(ins) for ins in inserts]
    for d in frame_interiors:
        if d not in insert_dims and (d[1], d[0]) not in insert_dims:
            msgs.append(f"no insert matches frame interior {d}")
    if frame_interiors and not any(((d[1], d[0]) in insert_dims and d not in insert_dims) for d in frame_interiors):
        msgs.append("no frame requires a visible 90-degree insert rotation")
    if h > 30 or w > 30:
        msgs.append("grid exceeds ARC max size")
    return msgs
