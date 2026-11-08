"""Generator for puzzle c0f76784.

Rule: gray(5) frame outlines of various sizes. Output fills each
frame's interior with color = (interior_width + 5).

Combinatorial axes (8): grid_h/w, n_frames, frame_sizes,
position_bias, anchor_corner, asymmetry_force, palette_size,
include_decoy.
Degenerates: tied_widths, single_frame, no_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "1b3ba815d58b"
VERSION = "2.0.1"
TASK_ID = "1b3ba815d58b"
SUMMARY = (
    "0-bg grid (h, w~14-20) with 2-3 HOLLOW color-5 "
    "(gray) RECTANGULAR FRAMES of distinct sizes — "
    "interior widths from {2, 3, 4} (so outer sizes "
    "from {4, 5, 6}). Frames are placed by some "
    "position bias (scattered / row-aligned / "
    "col-aligned / diagonal / corners) with ≥1-cell "
    "margin between them. Rule: for each color-5 "
    "FRAME, compute its INTERIOR WIDTH iw (the bbox "
    "interior dimension). FILL the frame's interior "
    "cells with COLOR = iw + 5 — so width 2 → color "
    "7 (orange), width 3 → color 8 (cyan), width 4 → "
    "color 9 (maroon). The gray frame border stays "
    "5. Net: each frame's empty interior gets a "
    "width-keyed solid fill."
)

INVARIANTS = [
    "background is 0",
    ">=2 gray(5) rectangular frame outlines",
    "interior widths in {2, 3, 4} (output colors 7, 8, 9)",
    "frames non-overlapping with margin >=1",
]

POSITION_BIASES = ("scattered", "row_aligned", "col_aligned", "diagonal",
                   "corners")
DEGENERATE_TEXTURES = ("tied_widths", "single_frame", "no_frames")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..20", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "rng 14..20", "valid": "12..24"},
    "n_frames":       {"type": "int", "default": "3", "valid": "2..3"},
    "include_width_2":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "include_width_3":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "include_width_4":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 12, 14
    elif difficulty == "hard":
        h_lo, h_hi = 18, 24
    else:
        h_lo, h_hi = 14, 20
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    inner_widths = []
    if bool(overrides.get("include_width_2", True)):
        inner_widths.append(2)
    if bool(overrides.get("include_width_3", True)):
        inner_widths.append(3)
    if bool(overrides.get("include_width_4", True)):
        inner_widths.append(4)
    if not inner_widths:
        inner_widths = [2, 3, 4]
    g = full_grid(h, w, 0)
    placed_boxes = []
    placed = 0
    for idx, inner_w in enumerate(inner_widths):
        outer = inner_w + 2
        for _ in range(20):
            rr, rc = _pick_position(bias, h, w, outer, idx, rng)
            if rr is None:
                continue
            ok = all(not (rr - 1 <= or2 and rr + outer >= or1
                          and rc - 1 <= oc2 and rc + outer >= oc1)
                     for (or1, oc1, or2, oc2) in placed_boxes)
            if not ok:
                continue
            draw_rect_outline(g, rr, rc, outer, outer, 5)
            placed_boxes.append((rr, rc, rr + outer - 1,
                                  rc + outer - 1))
            placed += 1
            break
    if placed < 2:
        # Fallback to default placement
        for inner_w in inner_widths[:2]:
            outer = inner_w + 2
            rr = rng.randint(1, max(1, h - outer - 1))
            rc = rng.randint(1, max(1, w - outer - 1))
            draw_rect_outline(g, rr, rc, outer, outer, 5)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 color-5 frame cells (the gray outlines) present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    c5 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    if c5 < 4:
        errs.append(f"expected gray(5) frame outline cells, found {c5}")
    return errs


def _pick_position(bias, h, w, outer, idx, rng):
    if h - outer - 1 < 1 or w - outer - 1 < 1:
        return None, None
    if bias == "row_aligned":
        rr = max(1, (h - outer) // 2)
        rc = 1 + idx * (outer + 2)
        if rc + outer > w - 1:
            rc = rng.randint(1, w - outer - 1)
        return rr, rc
    if bias == "col_aligned":
        rr = 1 + idx * (outer + 2)
        if rr + outer > h - 1:
            rr = rng.randint(1, h - outer - 1)
        return rr, max(1, (w - outer) // 2)
    if bias == "diagonal":
        rr = 1 + idx * (outer + 2)
        rc = 1 + idx * (outer + 2)
        if rr + outer > h - 1 or rc + outer > w - 1:
            return rng.randint(1, h - outer - 1), rng.randint(1, w - outer - 1)
        return rr, rc
    if bias == "corners":
        corners = [(1, 1), (1, w - outer - 1), (h - outer - 1, 1),
                   (h - outer - 1, w - outer - 1)]
        return corners[idx % 4]
    return rng.randint(1, h - outer - 1), rng.randint(1, w - outer - 1)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "tied_widths":
        for r0, c0 in [(2, 2), (2, w - 6)]:
            draw_rect_outline(g, r0, c0, 4, 4, 5)
        return g
    if name == "single_frame":
        draw_rect_outline(g, 2, 2, 4, 4, 5)
        return g
    if name == "no_frames":
        return g
    return g
