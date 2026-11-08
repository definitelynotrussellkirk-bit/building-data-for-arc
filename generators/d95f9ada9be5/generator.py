"""Generator for v3_rich_schema:medium_03_fill_keyed_rectangle_holes — fill keyed-frame interior with 8.

Rule: 2 hollow rectangle frames in distinct colors. A lone marker
elsewhere matches one of the frame colors — that frame's interior
gets filled with 8. The other frame is unchanged.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_match, marker_matches_both.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "d95f9ada9be5"
VERSION = "1.2.0"
TASK_ID = "d95f9ada9be5"
SUMMARY = "2 hollow rect frames in distinct colors + 1 lone marker matching one frame's color."

INVARIANTS = [
    "background is 0",
    "exactly 2 full-perimeter rectangle frames (each ≥4×4) in distinct non-bg, non-8 colors",
    "exactly one isolated single-cell marker matching the color of exactly one frame",
    "frames and marker don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_match", "marker_matches_both")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "2", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "two_frames_one_marker",
                       "valid": "two_frames_one_marker"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 17)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")
    palette = list(random_palette(rng, 2, exclude={8}))
    for _outer in range(120):
        g = full_grid(h, w, 0)
        placed: list[tuple[int, int, int, int, int]] = []
        for color in palette:
            placed_one = False
            for _ in range(120):
                rh = rng.randint(4, 5)
                rw = rng.randint(4, 5)
                r1 = rng.randint(0, h - rh)
                c1 = rng.randint(0, w - rw)
                r2 = r1 + rh - 1
                c2 = c1 + rw - 1
                bb_pad = (r1 - 1, c1 - 1, r2 + 1, c2 + 1)
                if any(bbox_overlaps(bb_pad, (p[1] - 1, p[2] - 1, p[3] + 1, p[4] + 1)) for p in placed):
                    continue
                draw_frame(g, r1, c1, r2, c2, color)
                placed.append((color, r1, c1, r2, c2))
                placed_one = True
                break
            if not placed_one:
                break
        if len(placed) != 2:
            continue
        keyed = palette[rng.randint(0, 1)]
        marker_candidates = [(r, c) for r in range(h) for c in range(w)
                             if g[r][c] == 0 and not any(r1 - 1 <= r <= r2 + 1 and c1 - 1 <= c <= c2 + 1
                                                         for _, r1, c1, r2, c2 in placed)]
        rng.shuffle(marker_candidates)
        if not marker_candidates:
            continue
        mr, mc = marker_candidates[0]
        g[mr][mc] = keyed
        return g
    raise ValueError("could not place two keyed frames plus an isolated marker")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # Frames present but no marker — rule has no frame to select.
        draw_frame(g, 1, 1, 4, 5, 3)
        draw_frame(g, 1, 7, 4, 11, 4)
        return g
    if name == "no_match":
        # Marker color matches neither frame — rule has no frame to fill.
        draw_frame(g, 1, 1, 4, 5, 3)
        draw_frame(g, 1, 7, 4, 11, 4)
        g[8][3] = 6
        return g
    if name == "marker_matches_both":
        # Two frames share the same color — marker matches both, ambiguous.
        draw_frame(g, 1, 1, 4, 5, 3)
        draw_frame(g, 1, 7, 4, 11, 3)
        g[8][3] = 3
        return g
    return g


def _rect_frames(grid):
    h, w = len(grid), len(grid[0])
    frames = []
    for color in {v for row in grid for v in row if v}:
        for r1 in range(h):
            for c1 in range(w):
                for r2 in range(r1 + 3, h):
                    for c2 in range(c1 + 3, w):
                        ok = True
                        for c in range(c1, c2 + 1):
                            if grid[r1][c] != color or grid[r2][c] != color:
                                ok = False
                                break
                        if not ok:
                            continue
                        for r in range(r1, r2 + 1):
                            if grid[r][c1] != color or grid[r][c2] != color:
                                ok = False
                                break
                        if not ok:
                            continue
                        for r in range(r1 + 1, r2):
                            for c in range(c1 + 1, c2):
                                if grid[r][c] != 0:
                                    ok = False
                                    break
                            if not ok:
                                break
                        if ok:
                            frames.append((color, r1, c1, r2, c2))
    return frames


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    frames = _rect_frames(grid)
    if len(frames) != 2:
        msgs.append(f"expected exactly two hollow frames, found {len(frames)}")
        return msgs
    frame_colors = [f[0] for f in frames]
    if len(set(frame_colors)) != 2:
        msgs.append("frame colors are not distinct")
    perimeter = set()
    for _, r1, c1, r2, c2 in frames:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r in (r1, r2) or c in (c1, c2):
                    perimeter.add((r, c))
    markers = [(grid[r][c], r, c) for r in range(len(grid)) for c in range(len(grid[0]))
               if grid[r][c] != 0 and (r, c) not in perimeter]
    if len(markers) != 1:
        msgs.append(f"expected one isolated marker, found {len(markers)}")
    elif frame_colors.count(markers[0][0]) != 1:
        msgs.append("marker color does not select exactly one frame")
    return msgs
