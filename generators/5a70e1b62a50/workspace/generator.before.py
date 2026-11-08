"""Generator for arc_additional_puzzles_21_set11_bundle:E76.

Rule: closed same-color frames have their zero interiors filled with the frame color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, open_frame, frame_at_border.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "5a70e1b62a50"
VERSION = "2.1.0"  # deterministic fallback keeps requested hard two-frame cases from collapsing to one
TASK_ID = "5a70e1b62a50"
SUMMARY = (
    "0-bg grid (h~7-11, w~8-13) with "
    "1-2 CLOSED RECTANGULAR FRAMES "
    "(4-7 rows × 4-8 cols hollow "
    "rectangles), each in a DISTINCT "
    "non-zero color. Frames have "
    "non-overlapping bboxes with "
    "1-cell margin, NOT touching the "
    "grid border. Frame interiors are "
    "all 0. Rule (FILL ENCLOSED "
    "INTERIORS): identify each CLOSED "
    "RECTANGULAR FRAME (rectangle "
    "outline with all-0 interior). "
    "FILL every 0-CELL in the "
    "FRAME's INTERIOR (cells inside "
    "the bbox but not on the edge) "
    "with the FRAME's COLOR. The "
    "frame's edge cells stay. Cells "
    "outside any frame stay 0. Net: "
    "each hollow frame becomes "
    "filled-solid in its own color."
)

INVARIANTS = [
    "background is 0",
    "each nonzero object is a closed rectangular frame",
    "frame interiors are zero and do not touch the grid border",
    "each enclosed zero region has exactly one neighboring color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "open_frame", "frame_at_border")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "6..16"},
    "frame_count":    {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "scattered_closed_frames",
                       "valid": "scattered_closed_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _overlaps_with_margin(a, b, margin=1):
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return not (
        ar2 + margin < br1
        or br2 + margin < ar1
        or ac2 + margin < bc1
        or bc2 + margin < ac1
    )


def _candidate_frames(h, w, frames):
    out = []
    for rh in range(4, min(7, h - 2) + 1):
        for rw in range(4, min(8, w - 2) + 1):
            for r1 in range(1, h - rh):
                for c1 in range(1, w - rw):
                    bbox = (r1, c1, r1 + rh - 1, c1 + rw - 1)
                    if all(not _overlaps_with_margin(bbox, other) for other in frames):
                        out.append(bbox)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        frame_count = ctx.draw_int("frame_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 15)
        frame_count = ctx.draw_int("frame_count", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 8, 13)
        frame_count = ctx.draw_int("frame_count", 1, 2)
    colors = ctx.draw_distinct_colors("colors", n=frame_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    if frame_count == 2:
        # Pick the two frames jointly.  Sequential sampling can paint a large
        # first frame that leaves no legal second slot even though many valid
        # two-frame layouts exist for the canvas (hard collapsed to one frame on
        # ~37% of seeds).  Joint enumeration keeps the requested branch covered.
        candidates = _candidate_frames(h, w, [])
        rng.shuffle(candidates)
        chosen = None
        for b1 in candidates:
            partners = [b2 for b2 in candidates if not _overlaps_with_margin(b1, b2)]
            if partners:
                chosen = (b1, rng.choice(partners))
                break
        if chosen:
            b1, b2 = chosen
            draw_frame(g, *b1, colors[0])
            draw_frame(g, *b2, colors[1])
            return g

    frames = []
    for color in colors:
        placed = False
        for _ in range(200):
            rh = rng.randint(4, min(7, h - 2))
            rw = rng.randint(4, min(8, w - 2))
            r1 = rng.randint(1, h - rh - 1)
            c1 = rng.randint(1, w - rw - 1)
            bbox = (r1, c1, r1 + rh - 1, c1 + rw - 1)
            if all(not _overlaps_with_margin(bbox, other) for other in frames):
                draw_frame(g, *bbox, color)
                frames.append(bbox)
                placed = True
                break
        if not placed:
            # The random sampler can miss the remaining slot on hard examples,
            # silently collapsing a requested two-frame instance into one frame.
            # Exhaustively enumerate valid non-overlapping bboxes as a fallback;
            # shuffle first so the fallback remains seed-diverse.
            candidates = _candidate_frames(h, w, frames)
            rng.shuffle(candidates)
            if candidates:
                bbox = candidates[0]
                draw_frame(g, *bbox, color)
                frames.append(bbox)
                placed = True
        if not placed:
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Empty grid — rule has no frames to fill.
        return g
    if name == "open_frame":
        # 3-walls of a rectangle (one missing) — rule's "closed
        # frame" filter excludes; output equals input.
        for c in range(2, 7): g[2][c] = 4
        for r in range(2, 6): g[r][2] = 4
        for r in range(2, 6): g[r][6] = 4
        return g
    if name == "frame_at_border":
        # Frame placed flush against the grid border — rule's
        # "interior touches border" precondition violated; the
        # frame's interior region is part of the unbounded "outside".
        draw_frame(g, 0, 0, 5, 6, 4)
        return g
    return g


def _find_closed_frames(grid):
    frames = []
    colors = sorted({v for row in grid for v in row if v != 0})
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
        if not cells:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r2 - r1 + 1 < 4 or c2 - c1 + 1 < 4:
            continue
        outline = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                   if r in (r1, r2) or c in (c1, c2)}
        interior = {(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)}
        if cells == outline and all(grid[r][c] == 0 for r, c in interior):
            frames.append((color, r1, c1, r2, c2))
    return frames


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is not rectangular"]
    frames = _find_closed_frames(grid)
    if not (1 <= len(frames) <= 2):
        msgs.append(f"expected 1-2 closed frames, found {len(frames)}")
    if difficulty == "hard" and len(frames) != 2:
        msgs.append(f"hard difficulty should realize two frames, found {len(frames)}")
    for i, (_, r1, c1, r2, c2) in enumerate(frames):
        if r1 == 0 or c1 == 0 or r2 == len(grid) - 1 or c2 == len(grid[0]) - 1:
            msgs.append(f"frame {i} touches the grid border")
    for i, a in enumerate(frames):
        for b in frames[i + 1:]:
            if _overlaps_with_margin(a[1:], b[1:]):
                msgs.append("frames overlap or lack the required one-cell margin")
    return msgs
