"""Generator for v2_meta_puzzles:E5 — fill each hollow box.

The input contains one through three separated monochromatic rectangular
outlines.  The Racket rule fills every cell strictly inside each component's
bounding box with that component's color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "1a5c1ca86025"
TASK_ID = "1a5c1ca86025"
VERSION = "3.0.0"
RULE_HASH = "85ff67d41b51"
SUMMARY = (
    "Fill the zero-valued interior of every separated monochromatic hollow "
    "rectangular outline with that outline's own color."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "there are 1-3 non-touching monochromatic rectangular outlines",
    "every outline is at least 3x3 and has an all-zero interior",
    "outline colors are distinct, so each object keeps its own fill color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "difficulty/sample-index schedule", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "difficulty/sample-index schedule", "valid": "9..20"},
    "n_rects": {"type": "int", "default": "lesson schedule: 1..3", "valid": "1..3"},
    "palette_kind": {"type": "str", "default": "keyed choice", "valid": "default|warm|cool|varied"},
}

# The first color is unique across palettes, so even a one-frame explicit
# palette override has an observable effect.  Later colors remain distinct.
_PALETTES = {
    "default": (4, 7, 5),
    "warm": (2, 6, 9),
    "cool": (1, 3, 8),
    "varied": (9, 5, 2),
}
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty first row"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC color integers 0..9"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            start = (row, col)
            if color == 0 or start in seen:
                continue
            seen.add(start)
            cells = {start}
            stack = [start]
            while stack:
                current_row, current_col = stack.pop()
                for dr, dc in _ORTHOGONAL:
                    neighbour = current_row + dr, current_col + dc
                    if (
                        0 <= neighbour[0] < height
                        and 0 <= neighbour[1] < width
                        and neighbour not in seen
                        and grid[neighbour[0]][neighbour[1]] == color
                    ):
                        seen.add(neighbour)
                        cells.add(neighbour)
                        stack.append(neighbour)
            result.append((color, frozenset(cells)))
    return tuple(result)


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _border_cells(row0, col0, row1, col1):
    return frozenset(
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    )


def _analysis(grid):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "frames": ()}
    height, width = len(grid), len(grid[0])
    errors = []
    if not (9 <= height <= 18 and 9 <= width <= 20):
        errors.append(f"dimensions {height}x{width} outside 9..18 x 9..20")
    components = _components(grid)
    if not 1 <= len(components) <= 3:
        errors.append(f"expected 1-3 non-zero components, found {len(components)}")
    colors = [color for color, _ in components]
    if len(set(colors)) != len(colors):
        errors.append("frame colors must be distinct")

    frames = []
    for color, cells in components:
        row0, col0, row1, col1 = _bbox(cells)
        if row1 - row0 < 2 or col1 - col0 < 2:
            errors.append(f"color {color} has no strict bbox interior")
            continue
        expected = _border_cells(row0, col0, row1, col1)
        if cells != expected:
            missing = len(expected - cells)
            extra = len(cells - expected)
            errors.append(
                f"color {color} is not an exact hollow rectangle "
                f"(missing border={missing}, extra interior/non-border={extra})"
            )
            continue
        if any(
            grid[row][col] != 0
            for row in range(row0 + 1, row1)
            for col in range(col0 + 1, col1)
        ):
            errors.append(f"color {color} rectangle interior is not zero")
        frames.append(
            {
                "color": color,
                "cells": cells,
                "bbox": (row0, col0, row1, col1),
                "height": row1 - row0 + 1,
                "width": col1 - col0 + 1,
                "interior_area": (row1 - row0 - 1) * (col1 - col0 - 1),
            }
        )

    # The lesson grammar promises a full one-cell background moat.  This is
    # stronger than mere 4-connectivity and prevents diagonal/tangent scenes.
    for index, left in enumerate(frames):
        for right in frames[index + 1 :]:
            if any(
                max(abs(row - other_row), abs(col - other_col)) <= 1
                for row, col in left["cells"]
                for other_row, other_col in right["cells"]
            ):
                errors.append(
                    f"colors {left['color']} and {right['color']} lack a one-cell buffer"
                )
    return {"errors": errors, "frames": tuple(frames)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons rather than merely checking palette/shape."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    """Recover the exact semantic count axis from the returned grid."""
    return {"n_rects": len(_components(grid))}


def rule_mirror(grid):
    """Independent test helper; generation never uses this output oracle."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [list(row) for row in grid]
    for frame in analysis["frames"]:
        row0, col0, row1, col1 = frame["bbox"]
        for row in range(row0 + 1, row1):
            for col in range(col0 + 1, col1):
                out[row][col] = frame["color"]
    return out


def _scheduled_count(sample_index, difficulty):
    phase = sample_index % 4
    if difficulty == "easy":
        return 1 if phase == 0 else 2
    if difficulty == "hard":
        return 3 if phase in (0, 3) else 2
    return 2


def _draw_dimensions(ctx, difficulty, overrides):
    if overrides.get("grid_h") is not None:
        height = ctx.draw_int("grid_h", 9, 18)
    elif difficulty == "easy":
        height = ctx.draw_int("grid_h", 9, 11)
    elif difficulty == "hard":
        height = ctx.draw_int("grid_h", 13, 18)
    else:
        height = ctx.draw_int("grid_h", 10, 14)

    if overrides.get("grid_w") is not None:
        width = ctx.draw_int("grid_w", 9, 20)
    elif difficulty == "easy":
        width = ctx.draw_int("grid_w", 9, 12)
    elif difficulty == "hard":
        width = ctx.draw_int("grid_w", 14, 20)
    else:
        width = ctx.draw_int("grid_w", 11, 15)
    return height, width


def _draw_count(ctx, sample_index, difficulty, overrides):
    if overrides.get("n_rects") is not None:
        return ctx.draw_int("n_rects", 1, 3)
    scheduled = _scheduled_count(sample_index, difficulty)
    return ctx.draw_int("n_rects", scheduled, scheduled)


def _slots(height, width, count, rng):
    """Partition the canvas into count regions separated by a one-cell moat."""
    if count == 1:
        return [(0, 0, height - 1, width - 1)]
    if count == 2:
        if rng.choice((False, True)):
            split = rng.randint(3, width - 4)
            return [(0, 0, height - 1, split - 1), (0, split + 1, height - 1, width - 1)]
        split = rng.randint(3, height - 4)
        return [(0, 0, split - 1, width - 1), (split + 1, 0, height - 1, width - 1)]

    orientation = rng.randrange(4)
    if orientation in (0, 1):
        row_split = rng.randint(3, height - 4)
        col_split = rng.randint(3, width - 4)
        top_left = (0, 0, row_split - 1, col_split - 1)
        top_right = (0, col_split + 1, row_split - 1, width - 1)
        bottom = (row_split + 1, 0, height - 1, width - 1)
        slots = [top_left, top_right, bottom]
        if orientation == 1:
            slots = [
                (height - 1 - r1, c0, height - 1 - r0, c1)
                for r0, c0, r1, c1 in slots
            ]
        return slots

    row_split = rng.randint(3, height - 4)
    col_split = rng.randint(3, width - 4)
    top = (0, 0, row_split - 1, col_split - 1)
    bottom = (row_split + 1, 0, height - 1, col_split - 1)
    right = (0, col_split + 1, height - 1, width - 1)
    slots = [top, bottom, right]
    if orientation == 3:
        slots = [
            (r0, width - 1 - c1, r1, width - 1 - c0)
            for r0, c0, r1, c1 in slots
        ]
    return slots


def _frame_in_slot(slot, rng, difficulty, frame_index, sample_index):
    row0, col0, row1, col1 = slot
    slot_h, slot_w = row1 - row0 + 1, col1 - col0 + 1
    if difficulty == "easy":
        max_h, max_w = min(slot_h, 5), min(slot_w, 5)
    elif difficulty == "hard":
        max_h, max_w = slot_h, slot_w
    else:
        max_h, max_w = min(slot_h, 7), min(slot_w, 7)

    # Cycle deterministic shape emphases so every lesson family contains
    # square and non-square interiors rather than relying on a lucky seed.
    phase = (sample_index + frame_index) % 4
    if phase == 0:
        frame_h = 3
        frame_w = rng.randint(3, max_w)
    elif phase == 1:
        frame_h = rng.randint(3, max_h)
        frame_w = 3
    elif phase == 2:
        side = rng.randint(3, min(max_h, max_w))
        frame_h = frame_w = side
    else:
        frame_h = rng.randint(3, max_h)
        frame_w = rng.randint(3, max_w)
    top = rng.randint(row0, row1 - frame_h + 1)
    left = rng.randint(col0, col1 - frame_w + 1)
    return top, left, top + frame_h - 1, left + frame_w - 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width = _draw_dimensions(ctx, difficulty, overrides)
    count = _draw_count(ctx, sample_index, difficulty, overrides)
    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    colors = _PALETTES[palette_kind][:count]
    layout_rng = ctx.draw_rng("layout")

    grid = full_grid(height, width, 0)
    slots = _slots(height, width, count, layout_rng)
    # Shuffle object-to-region assignment without changing the guaranteed moat.
    layout_rng.shuffle(slots)
    for index, (slot, color) in enumerate(zip(slots, colors)):
        row0, col0, row1, col1 = _frame_in_slot(
            slot, layout_rng, difficulty, index, sample_index
        )
        draw_frame(grid, row0, col0, row1, col1, color)

    errors = self_check(grid)
    if errors:
        raise ValueError(f"internal E5 construction violated invariants: {errors}")
    return grid
