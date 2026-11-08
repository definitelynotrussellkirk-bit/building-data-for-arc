"""Generator for ARC task 7860069b4149 — sweep a component away from 9.

A single maroon anchor (9) sits immediately outside one side of a connected,
monochrome component.  Translate the complete component one cell at a time in
the direction away from the anchor, painting every valid translated copy until
the next copy would leave the grid.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7860069b4149"
VERSION = "2.0.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "One connected monochrome component and one color-9 anchor immediately "
    "outside its bounding box; sweep the whole component away from the anchor "
    "to the wall, preserving holes and concavities."
)

INVARIANTS = [
    "background is 0 and all cells are exact ARC colors",
    "exactly one color-9 anchor and one nonempty 4-connected monochrome component",
    "the anchor is one cell outside exactly one bounding-box side and aligned with that side",
    "there is room for at least one whole-component translation away from the anchor",
]

ANCHOR_SIDES = ("left", "right", "top", "bottom")
SHAPES = {
    "l3": ((0, 0), (0, 1), (1, 0)),
    "square4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "zigzag4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "l5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "hollow_box": (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
    "wide_u": (
        (0, 0),                         (0, 4),
        (1, 0),                         (1, 4),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
    ),
}
SHAPE_KINDS = tuple(SHAPES)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {"type": "int", "default": "rng 5..30", "valid": "5..30"},
    "grid_w": {"type": "int", "default": "rng 5..30", "valid": "5..30"},
    "anchor_side": {
        "type": "str", "default": "rng",
        "valid": "|".join(ANCHOR_SIDES),
    },
    "shape_kind": {
        "type": "str", "default": "rng",
        "valid": "|".join(SHAPE_KINDS),
    },
    "foreground_color": {"type": "int", "default": "rng 1..8", "valid": "1..8"},
    "sweep_steps": {"type": "int", "default": "rng 1..maximum lawful", "valid": "1..27"},
}


def _shape_size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _analyze(grid):
    """Return ``(errors, facts)`` for the exact canonical input grammar."""
    errors = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a nonempty rectangular list of rows"], None
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be a nonempty rectangular list of rows"], None
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be within 1..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid cells must be exact integer colors 0..9")
        return errors, None

    anchors = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 9]
    cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] not in (0, 9)]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-9 anchor, got {len(anchors)}")
    if not cells:
        errors.append("expected one nonempty foreground component")
    colors = {grid[r][c] for r, c in cells}
    if len(colors) > 1:
        errors.append("foreground component must be monochrome")
    if cells and not _connected(cells):
        errors.append("foreground cells must form one 4-connected component")
    if len(anchors) != 1 or not cells:
        return errors, None

    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    ar, ac = anchors[0]
    side_matches = []
    if ac == c0 - 1 and r0 <= ar <= r1:
        side_matches.append(("left", 0, 1, width - 1 - c1))
    if ac == c1 + 1 and r0 <= ar <= r1:
        side_matches.append(("right", 0, -1, c0))
    if ar == r0 - 1 and c0 <= ac <= c1:
        side_matches.append(("top", 1, 0, height - 1 - r1))
    if ar == r1 + 1 and c0 <= ac <= c1:
        side_matches.append(("bottom", -1, 0, r0))
    if len(side_matches) != 1:
        errors.append(
            "anchor must be one cell outside exactly one component bounding-box side "
            "and aligned with that side"
        )
        return errors, None

    side, dr, dc, steps = side_matches[0]
    if steps < 1:
        errors.append("component needs room for at least one translation away from the anchor")
    facts = {
        "height": height,
        "width": width,
        "anchor": anchors[0],
        "cells": tuple(cells),
        "color": next(iter(colors)) if len(colors) == 1 else None,
        "bbox": (r0, c0, r1, c1),
        "anchor_side": side,
        "direction": (dr, dc),
        "steps": steps,
    }
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None):
    return _analyze(grid)[0]


def rule_mirror(grid):
    """Independent Python diagnostic for the fixed Racket rule's semantics."""
    errors, facts = _analyze(grid)
    if errors:
        raise ValueError("invalid sweep input: " + "; ".join(errors))
    output = deepcopy(grid)
    dr, dc = facts["direction"]
    for distance in range(1, facts["steps"] + 1):
        for row, col in facts["cells"]:
            output[row + dr * distance][col + dc * distance] = facts["color"]
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_strict("grid_h", 5, 30)
    width = ctx.draw_int_strict("grid_w", 5, 30)
    side = ctx.draw_choice("anchor_side", ANCHOR_SIDES)
    legal_shapes = tuple(
        name for name in SHAPE_KINDS
        if _shape_size(SHAPES[name])[0] <= height - 2
        and _shape_size(SHAPES[name])[1] <= width - 2
    )
    shape_kind = ctx.draw_choice("shape_kind", legal_shapes)
    color = ctx.draw_color_strict("foreground_color", exclude={0, 9})
    shape = SHAPES[shape_kind]
    shape_h, shape_w = _shape_size(shape)

    maximum_steps = (width - shape_w - 1) if side in ("left", "right") else (height - shape_h - 1)
    sweep_steps = ctx.draw_int_strict("sweep_steps", 1, maximum_steps)
    rng = ctx.draw_rng("placement")
    if side == "left":
        row0 = rng.randint(0, height - shape_h)
        col0 = width - shape_w - sweep_steps
    elif side == "right":
        row0 = rng.randint(0, height - shape_h)
        col0 = sweep_steps
    elif side == "top":
        row0 = height - shape_h - sweep_steps
        col0 = rng.randint(0, width - shape_w)
    else:
        row0 = sweep_steps
        col0 = rng.randint(0, width - shape_w)

    grid = full_grid(height, width, 0)
    for dr, dc in shape:
        grid[row0 + dr][col0 + dc] = color

    if side in ("left", "right"):
        align = rng.randrange(shape_h)
        anchor_row = row0 + align
        anchor_col = col0 - 1 if side == "left" else col0 + shape_w
    else:
        align = rng.randrange(shape_w)
        anchor_row = row0 - 1 if side == "top" else row0 + shape_h
        anchor_col = col0 + align
    grid[anchor_row][anchor_col] = 9

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator constructed an invalid grid: {errors}")
    return grid
