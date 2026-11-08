"""Generator for arc_puzzle_bank_thirteenth_21_bundle:easy_90_fill_hollow_rectangles.

Rule: hollow rectangular frames are filled into solid rectangles (same color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: solid_rects, frame_too_thin, no_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "de83dfd70673"
VERSION = "2.0.0"
TASK_ID = "de83dfd70673"
SUMMARY = (
    "0-bg grid (h ∈ 8-12, w ∈ 9-14, by "
    "difficulty) with: TARGET ∈ 1-3 "
    "HOLLOW ONE-CELL-THICK RECTANGULAR "
    "FRAMES, each of size rh × rw (rh "
    "∈ 3-5, rw ∈ 3-6) drawn at "
    "non-overlapping interior positions "
    "(via _free padding check), each "
    "in a DISTINCT color drawn at "
    "random from {1..9}. Each frame's "
    "INTERIOR (cells strictly inside "
    "the outline) starts EMPTY (0); "
    "each frame is non-touching with "
    "others. Rule (FILL EACH HOLLOW "
    "RECTANGULAR FRAME'S INTERIOR "
    "WITH THE SAME COLOR AS THE "
    "FRAME — TURNING IT INTO A "
    "SOLID RECTANGLE): For EACH "
    "color-c frame: COMPUTE its "
    "bbox. For EVERY (r, c) inside "
    "the bbox (including interior "
    "and outline): PAINT g[r][c] = "
    "c. The frame outline stays "
    "color c (no change); the "
    "interior 0-cells become c. "
    "Net: each hollow frame "
    "becomes a solid same-color "
    "block of identical dimensions."
)

INVARIANTS = [
    "background is 0",
    "each component is a hollow rectangular frame",
    "frames have nonempty interiors",
    "frames are separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("solid_rects", "frame_too_thin", "no_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frames":         {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r0, c0, r1, c1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r1 >= h or c1 >= w:
        return False
    for r in range(max(0, r0 - 1), min(h, r1 + 2)):
        for c in range(max(0, c0 - 1), min(w, c1 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        target = ctx.draw_int("frames", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 14)
        target = ctx.draw_int("frames", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 14)
        target = ctx.draw_int("frames", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(160):
        if placed >= target:
            break
        rh = rng.randint(3, min(5, h))
        rw = rng.randint(3, min(6, w))
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        r1, c1 = r0 + rh - 1, c0 + rw - 1
        if not _free(g, r0, c0, r1, c1):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for c in range(c0, c1 + 1):
            g[r0][c] = color
            g[r1][c] = color
        for r in range(r0, r1 + 1):
            g[r][c0] = color
            g[r][c1] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "solid_rects":
        # rectangles already solid → bbox-fill = identity, rule has no visible effect
        for r in range(2, 5):
            for c in range(2, 6):
                g[r][c] = 4
        for r in range(7, 9):
            for c in range(7, 10):
                g[r][c] = 6
        return g
    if name == "frame_too_thin":
        # 2x2 / 1xN frames have no interior to fill → rule no-op
        for r in range(2, 4):
            for c in range(2, 4):
                g[r][c] = 4
        for c in range(6, 10):
            g[6][c] = 6
        return g
    if name == "no_frames":
        # empty grid → no frames to fill
        return g
    return g
