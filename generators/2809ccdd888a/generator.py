"""Generator for additional_bank:E3.

Hollow color-6 rectangles are filled by the rule.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, solid_rects, frame_too_thin.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "2809ccdd888a"
VERSION = "2.0.1"
TASK_ID = "2809ccdd888a"
SUMMARY = (
    "0-bg grid (h~8-12, w~"
    "9-13) with 2-3 HOLLOW "
    "COLOR-6 (magenta) "
    "RECT-OUTLINE FRAMES, "
    "dims 3-5 × 3-5, placed "
    "non-overlapping with "
    "1-cell padding. Each "
    "frame has only its "
    "BORDER cells painted "
    "6 with a NONEMPTY "
    "0-INTERIOR. Rule "
    "(FILL HOLLOW 6-"
    "FRAME INTERIORS WITH "
    "6): For EACH COLOR-6 "
    "FRAME at (r1, c1) to "
    "(r2, c2): PAINT every "
    "INTERIOR cell (r, c) "
    "with r1 < r < r2 AND "
    "c1 < c < c2 in COLOR-"
    "6. Frame outlines stay. "
    "The hollow becomes "
    "solid magenta. Net: "
    "magenta frame outlines "
    "become solid magenta "
    "rectangles."
)

INVARIANTS = [
    "background is 0",
    "all target objects are hollow rectangular frames of color 6",
    "each frame has a nonempty interior",
    "frames do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "solid_rects", "frame_too_thin")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_frames":       {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_hollow_frames",
                       "valid": "separated_hollow_frames"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|solid_rects|frame_too_thin"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one color-6 cell (frame outline) present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_frames", "solid_rects", "frame_too_thin"):
        return []
    errs = []
    c6 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 6)
    if c6 == 0:
        errs.append("no color-6 frame cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n_frames = ctx.draw_int("n_frames", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
        n_frames = ctx.draw_int("n_frames", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 13)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    boxes: list[tuple[int, int, int, int]] = []
    for _ in range(n_frames):
        for _try in range(100):
            rh = rng.randint(3, 5)
            rw = rng.randint(3, 5)
            rr = rng.randint(0, h - rh)
            rc = rng.randint(0, w - rw)
            bb = (rr, rc, rr + rh - 1, rc + rw - 1)
            if any(not (bb[2] + 1 < ob[0] or ob[2] + 1 < bb[0]
                        or bb[3] + 1 < ob[1] or ob[3] + 1 < bb[1])
                   for ob in boxes):
                continue
            draw_rect_outline(g, rr, rc, rh, rw, 6)
            boxes.append(bb)
            break
    if not boxes:
        draw_rect_outline(g, 1, 1, 4, 4, 6)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # blank → no frames to fill
        return g
    if name == "solid_rects":
        # solid rects (no hollow interior) → "hollow frame" precondition fails
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 6
        for r in range(6, 9):
            for c in range(6, 9):
                g[r][c] = 6
        return g
    if name == "frame_too_thin":
        # 2-cell frame → no interior to fill
        g[1][1] = 6; g[1][2] = 6
        g[2][1] = 6; g[2][2] = 6
        return g
    return g
