"""Generate varied scenes for selecting the object whose dilation seals a hole.

Rule (verified from canonical Racket): for each object, compare its hole count to the
hole count of its 3x3-dilated ("halo") version; the chosen object is the one whose
hole DISAPPEARS under dilation (a small enclosed hole that the halo seals). Output is
that object cropped, recoloured 8.

The previous body was mislabelled ("rotate motif inside frame") and always drew a
fixed 4x4 colour-7 frame, so the sealed-hole object was always the same 4x4 ring ->
output never varied (distinct_out=1). This rewrite CONSTRUCTS a varied holed object —
a solid rectangle minus one interior cell (a single sealable hole) — plus solid
distractors (no hole). The holed object's shape, hence the output, varies.

Axes: grid size, holed-rect dims, removed interior cell, distractor count.
Degenerates: no_holed (only solids), big_hole (3+ wide hole not sealed by halo), single_object.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "615496fbe17b"
VERSION = "2.2.0"
TASK_ID = "615496fbe17b"

SUMMARY = ("One object has a single small enclosed hole that a 3x3 dilation seals (a solid "
           "rectangle minus one interior cell); the rest are solid. The rule outputs the "
           "halo-sealed object cropped, colour 8. The holed shape and its size vary.")

INVARIANTS = [
    "exactly one object has a single enclosed hole sealed by 3x3 dilation (rect minus 1 interior cell)",
    "all other objects are solid (no holes)",
    "objects are separated by background",
]

DEGENERATE_TEXTURES = ("no_holed", "big_hole", "single_object")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 11..15", "valid": "7..20"},
    "grid_w":     {"type": "int", "default": "rng 13..18", "valid": "9..22"},
    "rect_h":     {"type": "int", "default": "rng 3..7 holed-rect height", "valid": "3..8"},
    "rect_w":     {"type": "int", "default": "rng 3..7 holed-rect width", "valid": "3..8"},
    "n_distract": {"type": "int", "default": "rng 1..3 solid distractors", "valid": "1..4"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 6, 8),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _place(g, cells, r0, c0, color, occ):
    h, w = len(g), len(g[0])
    ac = [(r0 + r, c0 + c) for r, c in cells]
    for (r, c) in ac:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occ:
                    return False
    for (r, c) in ac:
        g[r][c] = color
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                occ.add((r + dr, c + dc))
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    texture = overrides.pop("texture", None)
    if texture is not None and texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(
            "texture must be default, warm, cool, varied, no_holed, big_hole, or single_object"
        )
    if texture in DEGENERATE_TEXTURES:
        if overrides:
            raise ValueError("degenerate texture cannot be combined with ordinary overrides")
        return _draw_from_degenerate(texture, None)
    if texture is not None:
        if "palette_kind" in overrides and overrides["palette_kind"] != texture:
            raise ValueError("texture and palette_kind disagree")
        overrides["palette_kind"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    def draw_axis(label, ordinary_low, ordinary_high, absolute_low, absolute_high):
        low, high = (
            (absolute_low, absolute_high)
            if label in overrides
            else (ordinary_low, ordinary_high)
        )
        return ctx.draw_int(label, low, high)

    if difficulty == "easy":
        h = draw_axis("grid_h", 9, 11, 7, 20)
        w = draw_axis("grid_w", 11, 13, 9, 22)
        rh = draw_axis("rect_h", 3, 5, 3, 8)
        rw = draw_axis("rect_w", 3, 5, 3, 8)
        n_distract = draw_axis("n_distract", 1, 2, 1, 4)
    elif difficulty == "hard":
        h = draw_axis("grid_h", 14, 18, 7, 20)
        w = draw_axis("grid_w", 16, 20, 9, 22)
        rh = draw_axis("rect_h", 5, 8, 3, 8)
        rw = draw_axis("rect_w", 5, 8, 3, 8)
        n_distract = draw_axis("n_distract", 2, 3, 1, 4)
    else:
        h = draw_axis("grid_h", 11, 15, 7, 20)
        w = draw_axis("grid_w", 13, 18, 9, 22)
        rh = draw_axis("rect_h", 3, 7, 3, 8)
        rw = draw_axis("rect_w", 3, 7, 3, 8)
        n_distract = draw_axis("n_distract", 1, 2, 1, 4)
    palette_kind = ctx.draw_choice("palette_kind", tuple(_PALETTES))
    rng = ctx.draw_rng("layout")

    if rh > h - 2 or rw > w - 2:
        raise ValueError("rect_h/rect_w must leave room for separation on the requested grid")

    # Retry the complete packing rather than silently dropping a requested object.
    for _scene_attempt in range(80):
        g = full_grid(h, w, 0)
        occ = set()
        cells = [(r, c) for r in range(rh) for c in range(rw)]
        interior = [(r, c) for r in range(1, rh - 1) for c in range(1, rw - 1)]
        hole = rng.choice(interior)
        holed = [p for p in cells if p != hole]
        colors = rng.sample(list(_PALETTES[palette_kind]), 1 + n_distract)
        placed = False
        for _ in range(200):
            r0 = rng.randint(0, h - rh)
            c0 = rng.randint(0, w - rw)
            if _place(g, holed, r0, c0, colors[0], occ):
                placed = True
                break
        if not placed:
            continue

        complete = True
        for i in range(n_distract):
            d = _motif(rng, rng.randint(3, 5))
            bh = max(r for r, _ in d) + 1
            bw = max(c for _, c in d) + 1
            placed_distractor = False
            for _ in range(160):
                r0 = rng.randint(0, h - bh)
                c0 = rng.randint(0, w - bw)
                if _place(g, d, r0, c0, colors[1 + i], occ):
                    placed_distractor = True
                    break
            if not placed_distractor:
                complete = False
                break
        if complete:
            return g
    raise RuntimeError(
        f"failed to pack {1 + n_distract} separated objects into {h}x{w}"
    )


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)

    def solid(r0, c0, rh, rw, color, hole=None):
        for r in range(rh):
            for c in range(rw):
                if (r, c) != hole:
                    g[r0 + r][c0 + c] = color

    if name == "no_holed":
        solid(2, 2, 3, 3, 4); solid(2, 8, 2, 3, 6)        # only solids -> no pick
        return g
    if name == "big_hole":
        # 5x5 ring with a 3x3 hole -> NOT sealed by a 3x3 dilation -> no pick
        for r in range(5):
            for c in range(5):
                if r in (0, 4) or c in (0, 4):
                    g[2 + r][2 + c] = 4
        return g
    # single_object -> one holed object alone (still the pick)
    solid(2, 2, 3, 3, 4, hole=(1, 1))
    return g



def _components_for_self_check(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _enclosed_holes_in_bbox(cells):
    cellset = set(cells)
    r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
    zeros = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if (r, c) not in cellset}
    seen = set(); holes = 0
    for z in list(zeros):
        if z in seen:
            continue
        stack = [z]; seen.add(z); touches_edge = False
        while stack:
            r, c = stack.pop()
            if r in (r1, r2) or c in (c1, c2):
                touches_edge = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in zeros and nb not in seen:
                    seen.add(nb); stack.append(nb)
        if not touches_edge:
            holes += 1
    return holes


def _dilate_square(cells, height: int, width: int):
    return {
        (row + delta_row, col + delta_col)
        for row, col in cells
        for delta_row in (-1, 0, 1)
        for delta_col in (-1, 0, 1)
        if 0 <= row + delta_row < height and 0 <= col + delta_col < width
    }


def selection_intermediate(grid: Any) -> dict[str, Any]:
    """Return the input-dependent object metrics used by the canonical rule."""
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
    ):
        raise ValueError("grid must be a nonempty rectangular list of rows")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC integers 0..9")

    height, width = len(grid), len(grid[0])
    metrics = []
    for index, (color, cells) in enumerate(_components_for_self_check(grid)):
        before = _enclosed_holes_in_bbox(cells)
        grown = _dilate_square(cells, height, width)
        after = _enclosed_holes_in_bbox(grown)
        row_min = min(row for row, _ in cells)
        row_max = max(row for row, _ in cells)
        col_min = min(col for _, col in cells)
        col_max = max(col for _, col in cells)
        metrics.append(
            {
                "index": index,
                "color": color,
                "cells": [list(cell) for cell in sorted(cells)],
                "holes_before": before,
                "holes_after": after,
                "bbox": [row_min, col_min, row_max, col_max],
                "bbox_height": row_max - row_min + 1,
                "bbox_width": col_max - col_min + 1,
                "area": len(cells),
            }
        )
    selected = [item for item in metrics if item["holes_before"] > item["holes_after"]]
    return {"object_metrics": metrics, "selected": selected[0] if len(selected) == 1 else None}


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket rule."""
    intermediate = selection_intermediate(grid)
    selected = intermediate["selected"]
    if selected is None:
        raise ValueError("canonical rule requires exactly one object whose hole count decreases")
    row_min, col_min, row_max, col_max = selected["bbox"]
    output = full_grid(row_max - row_min + 1, col_max - col_min + 1, 0)
    for row, col in selected["cells"]:
        output[row - row_min][col - col_min] = 8
    return output


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    comps = _components_for_self_check(grid)
    if len(comps) < 2:
        msgs.append("expected holed object plus at least one distractor")
    try:
        intermediate = selection_intermediate(deepcopy(grid))
    except ValueError as exc:
        return [str(exc)]
    metrics = intermediate["object_metrics"]
    qualifying = [item for item in metrics if item["holes_before"] > item["holes_after"]]
    if len(qualifying) != 1:
        msgs.append(f"expected exactly one object whose hole is sealed by dilation, got {len(qualifying)}")
    elif not (
        qualifying[0]["holes_before"] == 1 and qualifying[0]["holes_after"] == 0
    ):
        msgs.append(
            "selected object must have exactly one enclosed hole that dilation seals"
        )
    other_holed = [
        (item["color"], item["holes_before"], item["holes_after"])
        for item in metrics
        if item not in qualifying and item["holes_before"]
    ]
    if other_holed:
        msgs.append(f"distractors must be solid; found holed distractors {other_holed}")
    return msgs
