"""Generator for ARC task aa14c6a9f111 — draw outlines from corner pairs.

Each active color appears exactly twice at opposite corners of one axis-aligned
rectangle.  The target draws every rectangle outline on a fresh black canvas.
Generated lessons deliberately combine hollow and two-cell-thick rectangles so
that filling bounding boxes, joining arbitrary pairs, or copying the input are
not viable shortcuts.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa14c6a9f111"
TASK_ID = "aa14c6a9f111"
VERSION = "3.0.0"
RULE_HASH = "3f7149fda1ec"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "A black 7..16 by 7..16 grid contains 2..3 distinct colors, each in "
    "exactly two diagonally opposite cells of an axis-aligned rectangle. "
    "Rectangles are either spatially disjoint or form a strictly nested chain; "
    "their outlines never overlap.  At least one rectangle is hollow and at "
    "least one is two cells thick.  Draw every rectangle outline in its corner "
    "color on a fresh black canvas."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is color 0 and every cell is an ARC color 0..9",
    "there are exactly 2..3 active colors and each appears exactly twice",
    "each same-color pair occupies distinct rows and distinct columns",
    "the induced rectangle outlines are pairwise disjoint",
    "rectangles are either pairwise disjoint or a strictly nested chain",
    "every generated lesson includes a hollow rectangle; generation also includes a two-cell-thick distractor",
]

PALETTE_KINDS = ("low", "middle", "high", "mixed")
PALETTE_GROUPS = {
    "low": (1, 2, 3),
    "middle": (4, 5, 6),
    "high": (7, 8, 9),
}
LAYOUT_MODES = ("disjoint", "nested")
ORIENTATION_MODES = ("main", "anti", "mixed")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased draw over 7..16",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased draw over 7..16",
        "valid": "7..16",
    },
    "rectangles": {
        "type": "int",
        "default": "uniform draw over 2..3",
        "valid": "2..3",
    },
    "palette_kind": {
        "type": "str",
        "default": "uniform draw",
        "valid": "|".join(PALETTE_KINDS),
    },
    "layout_mode": {
        "type": "str",
        "default": "uniform draw",
        "valid": "|".join(LAYOUT_MODES),
    },
    "orientation_mode": {
        "type": "str",
        "default": "uniform draw",
        "valid": "|".join(ORIENTATION_MODES),
    },
}


def _outline(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    cells = {(r0, col) for col in range(c0, c1 + 1)}
    cells.update((r1, col) for col in range(c0, c1 + 1))
    cells.update((row, c0) for row in range(r0, r1 + 1))
    cells.update((row, c1) for row in range(r0, r1 + 1))
    return cells


def _strictly_contains(
    outer: tuple[int, int, int, int],
    inner: tuple[int, int, int, int],
) -> bool:
    return (
        outer[0] < inner[0]
        and outer[1] < inner[1]
        and outer[2] > inner[2]
        and outer[3] > inner[3]
    )


def _bbox_disjoint(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> bool:
    return (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _palette_kind(colors: Iterable[int]) -> str | None:
    groups = set()
    for color in colors:
        matches = [
            name for name, values in PALETTE_GROUPS.items() if color in values
        ]
        if len(matches) != 1:
            return None
        groups.add(matches[0])
    if len(groups) == 1:
        return next(iter(groups))
    return "mixed" if len(groups) >= 2 else None


def _orientation_for_cells(cells: list[tuple[int, int]]) -> str | None:
    if len(cells) != 2:
        return None
    first, second = sorted(cells)
    if first[0] == second[0] or first[1] == second[1]:
        return None
    return "main" if first[1] < second[1] else "anti"


def _orientation_mode(orientations: Iterable[str]) -> str | None:
    values = set(orientations)
    if values == {"main"}:
        return "main"
    if values == {"anti"}:
        return "anti"
    if values == {"main", "anti"}:
        return "mixed"
    return None


def _layout_mode(boxes: list[tuple[int, int, int, int]]) -> str | None:
    if all(_bbox_disjoint(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1 :]):
        return "disjoint"
    ordered = sorted(
        boxes,
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )
    if all(
        _strictly_contains(ordered[index], ordered[index + 1])
        for index in range(len(ordered) - 1)
    ):
        return "nested"
    return None


def _analyze(grid):
    errors: list[str] = []
    facts = {
        "grid_h": None,
        "grid_w": None,
        "rectangles": None,
        "palette_kind": None,
        "layout_mode": None,
        "orientation_mode": None,
        "boxes": [],
        "thin_rectangles": 0,
        "hollow_rectangles": 0,
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a nonempty rectangular list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return facts, ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return facts, ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be literal ARC colors 0..9")

    height = len(grid)
    facts["grid_h"], facts["grid_w"] = height, width
    if not 7 <= height <= 16 or not 7 <= width <= 16:
        errors.append("grid dimensions must each be in 7..16")

    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if isinstance(value, int) and not isinstance(value, bool) and value != 0:
                by_color[value].append((row, col))

    colors = sorted(by_color)
    facts["rectangles"] = len(colors)
    facts["palette_kind"] = _palette_kind(colors)
    if not 2 <= len(colors) <= 3:
        errors.append("there must be exactly 2..3 active colors")
    if facts["palette_kind"] is None:
        errors.append("active colors must belong to the declared palette families")

    boxes: list[tuple[int, int, int, int]] = []
    orientations: list[str] = []
    outlines: list[set[tuple[int, int]]] = []
    for color in colors:
        cells = by_color[color]
        if len(cells) != 2:
            errors.append(f"color {color} must appear exactly twice; got {len(cells)}")
            continue
        orientation = _orientation_for_cells(cells)
        if orientation is None:
            errors.append(
                f"color {color} must occupy diagonally opposite corners, not one row or column"
            )
            continue
        orientations.append(orientation)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        box = min(rows), min(cols), max(rows), max(cols)
        boxes.append(box)
        outlines.append(_outline(box))
        box_h = box[2] - box[0] + 1
        box_w = box[3] - box[1] + 1
        if box_h == 2 or box_w == 2:
            facts["thin_rectangles"] += 1
        if box_h >= 3 and box_w >= 3:
            facts["hollow_rectangles"] += 1

    facts["boxes"] = [list(box) for box in boxes]
    if len(boxes) == len(colors):
        facts["layout_mode"] = _layout_mode(boxes)
        facts["orientation_mode"] = _orientation_mode(orientations)
        if facts["layout_mode"] is None:
            errors.append(
                "rectangle bounding boxes must be pairwise disjoint or a strictly nested chain"
            )
        if facts["orientation_mode"] is None:
            errors.append("corner orientations must be main, anti, or a mix of both")
        for index, left in enumerate(outlines):
            for right in outlines[index + 1 :]:
                if left & right:
                    errors.append("rectangle outlines must not overlap")
                    break
            if errors and errors[-1] == "rectangle outlines must not overlap":
                break

    if facts["hollow_rectangles"] < 1:
        errors.append("at least one rectangle must have a hollow interior")
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict:
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "rectangles": facts["rectangles"],
        "palette_kind": facts["palette_kind"],
        "layout_mode": facts["layout_mode"],
        "orientation_mode": facts["orientation_mode"],
    }


def _choose_colors(ctx, palette_kind: str, count: int) -> list[int]:
    rng = ctx.draw_rng("colors")
    if palette_kind in PALETTE_GROUPS:
        colors = rng.sample(list(PALETTE_GROUPS[palette_kind]), count)
    elif count == 2:
        colors = [
            rng.choice(PALETTE_GROUPS["low"]),
            rng.choice(PALETTE_GROUPS["high"]),
        ]
    else:
        colors = [
            rng.choice(PALETTE_GROUPS["low"]),
            rng.choice(PALETTE_GROUPS["middle"]),
            rng.choice(PALETTE_GROUPS["high"]),
        ]
    rng.shuffle(colors)
    return colors


def _choose_orientations(ctx, mode: str, count: int) -> list[str]:
    if mode in ("main", "anti"):
        return [mode] * count
    orientations = ["main", "anti"]
    if count == 3:
        orientations.append(ctx.draw_rng("mixed_orientation_tail").choice(("main", "anti")))
    ctx.draw_rng("mixed_orientation_order").shuffle(orientations)
    return orientations


def _box_in_region(
    rng,
    region: tuple[int, int, int, int],
    *,
    hollow: bool,
) -> tuple[int, int, int, int]:
    top, left, bottom, right = region
    region_h = bottom - top + 1
    region_w = right - left + 1
    if hollow:
        box_h = rng.randint(3, region_h)
        box_w = rng.randint(3, region_w)
    elif rng.randrange(2) == 0:
        box_h = 2
        box_w = rng.randint(2, region_w)
    else:
        box_h = rng.randint(2, region_h)
        box_w = 2
    row0 = rng.randint(top, bottom - box_h + 1)
    col0 = rng.randint(left, right - box_w + 1)
    return row0, col0, row0 + box_h - 1, col0 + box_w - 1


def _disjoint_boxes(ctx, height: int, width: int, count: int):
    row_split = height // 2
    col_split = width // 2
    regions = [
        (0, 0, row_split - 1, col_split - 1),
        (0, col_split, row_split - 1, width - 1),
        (row_split, 0, height - 1, col_split - 1),
        (row_split, col_split, height - 1, width - 1),
    ]
    rng = ctx.draw_rng("disjoint_layout")
    rng.shuffle(regions)
    boxes = [_box_in_region(rng, regions[0], hollow=True)]
    boxes.extend(
        _box_in_region(rng, region, hollow=False)
        for region in regions[1:count]
    )
    rng.shuffle(boxes)
    return boxes


def _nested_boxes(ctx, height: int, width: int, count: int):
    rng = ctx.draw_rng("nested_layout")
    minimum = 7 if count == 3 else 5
    outer_h = rng.randint(minimum, height)
    outer_w = rng.randint(minimum, width)
    row0 = rng.randint(0, height - outer_h)
    col0 = rng.randint(0, width - outer_w)
    outer = (row0, col0, row0 + outer_h - 1, col0 + outer_w - 1)
    if count == 2:
        inner_row = rng.randint(outer[0] + 1, outer[2] - 2)
        inner_col = rng.randint(outer[1] + 1, outer[3] - 2)
        return [outer, (inner_row, inner_col, inner_row + 1, inner_col + 1)]

    middle = (outer[0] + 1, outer[1] + 1, outer[2] - 1, outer[3] - 1)
    inner_row = rng.randint(middle[0] + 1, middle[2] - 2)
    inner_col = rng.randint(middle[1] + 1, middle[3] - 2)
    return [outer, middle, (inner_row, inner_col, inner_row + 1, inner_col + 1)]


def _paint_corner_pair(
    grid: list[list[int]],
    box: tuple[int, int, int, int],
    color: int,
    orientation: str,
) -> None:
    r0, c0, r1, c1 = box
    if orientation == "main":
        first, second = (r0, c0), (r1, c1)
    else:
        first, second = (r0, c1), (r1, c0)
    grid[first[0]][first[1]] = color
    grid[second[0]][second[1]] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 7, 16)
    width = ctx.draw_int_diff("grid_w", 7, 16)
    count = ctx.draw_int("rectangles", 2, 3)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    layout_mode = ctx.draw_choice("layout_mode", LAYOUT_MODES)
    orientation_mode = ctx.draw_choice("orientation_mode", ORIENTATION_MODES)

    colors = _choose_colors(ctx, palette_kind, count)
    orientations = _choose_orientations(ctx, orientation_mode, count)
    if layout_mode == "disjoint":
        boxes = _disjoint_boxes(ctx, height, width, count)
    else:
        boxes = _nested_boxes(ctx, height, width, count)

    grid = full_grid(height, width, 0)
    for box, color, orientation in zip(boxes, colors, orientations):
        _paint_corner_pair(grid, box, color, orientation)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid
