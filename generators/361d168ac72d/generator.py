"""Generator for arc_puzzle_bank_21_next:medium_c01 — Recolor objects by aspect ratio.

Rule: for each object, paint with
  2 if obj-h > obj-w (tall)
  3 if obj-w > obj-h (wide)
  4 if equal (square-ish)

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_squares, all_same_orientation, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob, bbox_of, bbox_overlaps

GENERATOR_ID = "361d168ac72d"
VERSION = "1.2.0"  # +self_check
TASK_ID = "361d168ac72d"
SUMMARY = "Several non-touching blobs with varied aspect ratios; output recolors by tall/wide/square."

INVARIANTS = [
    "between 3 and 5 non-touching blobs",
    "at least one tall (h>w), one wide (w>h), one square-ish (h=w)",
    "blobs are bbox-isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_squares", "all_same_orientation", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 nonzero cell present (blob(s) placed on background)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    flat = [v for row in grid for v in row]
    if all(v == 0 for v in flat):
        errs.append("all-zero grid: no blobs placed")
    return errs


def _make_oriented(rng, h, w, used, target_size, orient):
    for _ in range(15):
        blob = grow_blob(rng, h, w, used, target_size)
        if blob is None: return None
        bb = bbox_of(blob)
        bh = bb[2] - bb[0] + 1
        bw = bb[3] - bb[1] + 1
        if orient == "tall" and bh > bw: return blob
        if orient == "wide" and bw > bh: return blob
        if orient == "square" and bh == bw: return blob
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_blobs = ctx.draw_int("n_blobs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_blobs = ctx.draw_int("n_blobs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_blobs = ctx.draw_int("n_blobs", 3, 5)

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set()
    bboxes = []
    colors = list(range(1, 10)); rng.shuffle(colors)

    required = ["tall", "wide", "square"]
    extras = ["tall", "wide", "square"]
    plan = required + rng.sample(extras, k=max(0, n_blobs - len(required)))

    for i, orient in enumerate(plan):
        size = rng.randint(3, 6)
        for attempt in range(10):
            blob = _make_oriented(rng, h, w, used, size, orient)
            if blob is None: continue
            bb = bbox_of(blob)
            if any(bbox_overlaps(bb, ob) for ob in bboxes):
                continue
            used |= blob
            bboxes.append(bb)
            color = colors[i % len(colors)]
            for r, c in blob: g[r][c] = color
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "all_squares":
        # all blobs square → output is monochrome 4, no orientation contrast
        for r in range(2, 4):
            for c in range(2, 4):
                g[r][c] = 5
        for r in range(6, 8):
            for c in range(6, 8):
                g[r][c] = 6
        return g
    if name == "all_same_orientation":
        # all blobs tall → output is monochrome 2, no contrast across orientations
        for r in range(1, 5):
            g[r][2] = 5
        for r in range(2, 6):
            g[r][7] = 6
        return g
    if name == "no_blobs":
        # empty grid → no objects to recolor
        return g
    return g
