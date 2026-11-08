"""Generator for 8ba14f53.

Rule: find the two side-by-side single-color objects, count background cells
strictly inside each bounding box, and pack those counts into a 3x3 summary
(left object first, right object beginning on the next unused row).

Combinatorial axes (8): grid_h/w, fw_l, fw_r, palette_kind,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: same_color, no_rects, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "8265382d9c72"
VERSION = "1.3.1"
TASK_ID = "8265382d9c72"
SUMMARY = "Two side-by-side colored objects; count interior background cells into a 3x3 summary."

INVARIANTS = [
    "exactly 2 side-by-side same-color 4-connected objects",
    "each object has a nonempty background interior inside its bounding box",
    "left-object count is packed first; right-object count starts on the next row",
    "both counts fit visibly in the 3x3 output summary",
]

POSITION_BIASES = ("scattered", "edge_aligned", "wide_spread", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("same_color", "no_rects", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "4..8"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "fw_l":           {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "fw_r":           {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _connected_objects(grid):
    """Mirror Racket ``objects g 0``: row-major, same-color, 4-connected."""
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            objects.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return objects


def _bbox_background_count(grid, bbox):
    r0, c0, r1, c1 = bbox
    return sum(
        grid[r][c] == 0
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the executable source rule, including irregular canonical objects."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    objects = _connected_objects(grid)
    if not objects:
        return [] if texture == "no_rects" else ["no colored objects found"]
    if len(objects) != 2:
        return [f"expected exactly 2 colored objects; found {len(objects)}"]
    if objects[0]["color"] == objects[1]["color"]:
        return ["expected the two objects to use distinct colors"]

    left, right = sorted(objects, key=lambda obj: obj["bbox"][1])
    errs = []
    if left["bbox"][3] >= right["bbox"][1]:
        errs.append("object bounding boxes are not side-by-side")

    counts = []
    for label, obj in (("left", left), ("right", right)):
        r0, c0, r1, c1 = obj["bbox"]
        if r1 - r0 < 2 or c1 - c0 < 2:
            errs.append(f"{label} object bbox is too small for an interior")
            counts.append(0)
            continue
        count = _bbox_background_count(grid, obj["bbox"])
        counts.append(count)
        if count <= 0:
            errs.append(f"{label} object has no interior background cells")

    if len(counts) == 2:
        n_left, n_right = counts
        if n_left > 9 or n_right > _visible_room_after_left(n_left):
            errs.append(
                f"interior counts do not fit the 3x3 summary: left={n_left} right={n_right}"
            )
    return errs


def _hole_count(rect_h, rect_w):
    return max(0, rect_h - 2) * max(0, rect_w - 2)


def _visible_room_after_left(n_left):
    """Cells available to the right-rectangle count in the canonical 3x3 output.

    The Racket rule writes the left count first, then starts the right count on
    the next row after the left block. If the right count exceeds this room, the
    target silently truncates the second rectangle, which makes synthetic pairs
    look constant and hides the intended counting rule.
    """
    row_start = (n_left + 2) // 3
    return max(0, 3 - row_start) * 3


def _rect_candidates(max_h, min_holes=1, max_holes=6):
    out = []
    for rh in range(3, min(max_h, 6) + 1):
        for rw in range(3, 6):
            n = _hole_count(rh, rw)
            if min_holes <= n <= max_holes:
                out.append((rh, rw, n))
    return out


def _choose_rect_pair(rng, grid_h, difficulty):
    """Choose rectangle dimensions whose hole counts are both visible.

    v1.1.0 used full-grid-height rectangles with independent widths. Easy
    examples often had equal hole counts, while hard examples often overflowed
    the canonical 3x3 answer so the right rectangle's count disappeared. Both
    regimes weaken the demos. Normal samples now enforce left_count <
    right_count and enough remaining cells to show the right count.
    """
    cands = _rect_candidates(grid_h)
    if difficulty == "easy":
        cands = [x for x in cands if x[2] <= 3] or cands
    elif difficulty == "hard":
        cands = [x for x in cands if x[2] >= 2] or cands
    pairs = []
    for left in cands:
        for right in cands:
            nl, nr = left[2], right[2]
            if nl < nr and nr <= _visible_room_after_left(nl):
                pairs.append((left, right))
    return rng.choice(pairs or [((3, 3, 1), (4, 4, 4))])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 5, 8, 10
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 6, 8, 12, 14
    else:
        h_lo, h_hi, w_lo, w_hi = 4, 6, 9, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, 2, rng)
    color_l, color_r = pal[0], pal[1]
    (fh_l, fw_l, n_l), (fh_r, fw_r, n_r) = _choose_rect_pair(rng, h, difficulty)

    # Preserve explicit width overrides only when they keep the canonical output
    # visible and non-truncated. Normal generation prioritizes pedagogy over an
    # invalid override.
    if "fw_l" in overrides:
        cand = max(3, min(int(overrides["fw_l"]), 5))
        n = _hole_count(fh_l, cand)
        if 0 < n < n_r and n_r <= _visible_room_after_left(n):
            fw_l, n_l = cand, n
    if "fw_r" in overrides:
        cand = max(3, min(int(overrides["fw_r"]), 5))
        n = _hole_count(fh_r, cand)
        if n_l < n and n <= _visible_room_after_left(n_l):
            fw_r, n_r = cand, n

    if fw_l + fw_r + 1 > w:
        w = fw_l + fw_r + 1
        g = full_grid(h, w, 0)
    c0_l = 0
    c0_r = w - fw_r
    draw_rect_outline(g, 0, c0_l, fh_l, fw_l, color_l)
    draw_rect_outline(g, 0, c0_r, fh_r, fw_r, color_r)
    assert 0 < n_l < n_r <= _visible_room_after_left(n_l), (n_l, n_r)
    return g

def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 5, 10
    g = full_grid(h, w, 0)
    if name == "same_color":
        draw_rect_outline(g, 0, 0, h, 3, 2)
        draw_rect_outline(g, 0, w - 3, h, 3, 2)
        return g
    if name == "no_rects":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
