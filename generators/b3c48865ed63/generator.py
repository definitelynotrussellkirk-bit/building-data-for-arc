"""Generator for arc_additional_puzzles_21_set9:M61 — fill interior holes of target-color rings.

Rule: cell (0, 0) holds the target color. Each connected component
of that color has its bbox-interior bg-holes filled with target,
leaving (0, 0) cleared in the output. Components in other colors
are untouched.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_target_color (cell (0,0) is bg → rule's selector
finds nothing to fill), no_target_components (target color only at
(0,0) → no rings to fill), filled_rings (target rings have no
interior holes → rule's fill is a no-op).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import RING_3X3
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "b3c48865ed63"
VERSION = "2.1.1"  # diversify: target rings were all the fixed RING_3X3. Rule
# fills the enclosed interior of ANY hollow object, so v2.1 uses variable-size
# hollow rectangular rings (3..5 per side) -> larger/varied filled interiors.
TASK_ID = "b3c48865ed63"
SUMMARY = "(0,0) holds the target color. Target-color rings (or other components with bg interiors) get their interior holes filled with target color. (0,0) is cleared in output. Non-target components untouched."

# Rivals: 'output is input' refuted by any demo with hollow rings.
# 'fill all components' refuted by any demo where distractor stays
# hollow. 'use bg for fill' refuted by any demo (fill = target).
# 'keep (0,0)' refuted by any demo (it's cleared to 0). 3 demos
# with mixed rings cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "(0, 0) holds the target color (any non-bg)",
    "1-2 connected components in target color, each with a bbox interior hole",
    "0-1 distractor components in another color (output leaves them untouched)",
    "objects don't touch each other or (0, 0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_target_color", "no_target_components", "filled_rings")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "9..20"},
    "n_target_rings": {"type": "int", "default": "rng 1..2", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "legend_plus_target_rings",
                       "valid": "legend_plus_target_rings"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: (0,0) is non-zero (target color stored there); ≥1 other cell with target color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    target = grid[0][0]
    if target == 0:
        errs.append("expected non-zero target color at (0,0); got 0")
        return errs
    target_cells = sum(1 for r in range(h) for c in range(w)
                       if grid[r][c] == target and (r, c) != (0, 0))
    if target_cells < 4:
        errs.append(f"expected ≥4 target-color({target}) cells beyond (0,0); found {target_cells}")
    return errs


def _hollow_ring(rng, max_h, max_w):
    """A hollow rectangular ring (border only) of variable size, >=3 each side
    so it has a non-empty interior. Returns (cells, bh, bw)."""
    bh = rng.randint(3, max_h)
    bw = rng.randint(3, max_w)
    cells = [(r, c) for r in range(bh) for c in range(bw)
             if r in (0, bh - 1) or c in (0, bw - 1)]
    return cells, bh, bw


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_target_rings", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 16, 20)
        n = ctx.draw_int("n_target_rings", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_target_rings", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = list(random_palette(rng, 2))
    target = palette[0]
    distractor = palette[1]
    g[0][0] = target
    placed: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)]
    max_rh = min(5, h - 3)
    max_rw = min(5, w - 2)
    for _ in range(n):
        for _ in range(60):
            cells, bh, bw = _hollow_ring(rng, max(3, max_rh), max(3, max_rw))
            r0 = rng.randint(2, h - 1 - bh)
            c0 = rng.randint(0, w - bw)
            bb = (r0 - 1, c0 - 1, r0 + bh, c0 + bw)
            if any(bbox_overlaps(bb, p) for p in placed): continue
            paint_at(g, r0, c0, cells, target)
            placed.append((r0, c0, r0 + bh - 1, c0 + bw - 1))
            break
    if rng.random() < 0.5:
        for _ in range(60):
            cells, bh, bw = _hollow_ring(rng, max(3, max_rh), max(3, max_rw))
            r0 = rng.randint(2, h - 1 - bh)
            c0 = rng.randint(0, w - bw)
            bb = (r0 - 1, c0 - 1, r0 + bh, c0 + bw)
            if any(bbox_overlaps(bb, p) for p in placed): continue
            paint_at(g, r0, c0, cells, distractor)
            placed.append((r0, c0, r0 + bh - 1, c0 + bw - 1))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_target_color":
        # (0,0) is bg — rule's "target color from (0,0)" lookup
        # picks bg; selector finds nothing to fill.
        paint_at(g, 3, 3, RING_3X3, 4)
        paint_at(g, 7, 8, RING_3X3, 6)
        return g
    if name == "no_target_components":
        # Target color only at (0,0) — no rings to fill;
        # rule's per-component loop is empty.
        g[0][0] = 4
        paint_at(g, 3, 3, RING_3X3, 6)
        paint_at(g, 7, 8, RING_3X3, 7)
        return g
    if name == "filled_rings":
        # Target ring is a solid 3x3 (no interior hole) — rule's
        # interior-fill is a no-op.
        g[0][0] = 4
        for r in range(3, 6):
            for c in range(3, 6):
                g[r][c] = 4
        paint_at(g, 7, 8, RING_3X3, 6)
        return g
    return g
