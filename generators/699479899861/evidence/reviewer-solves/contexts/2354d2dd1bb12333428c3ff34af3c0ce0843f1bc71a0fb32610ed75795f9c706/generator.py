"""Generator for ``Apply orthogonal closure to each red component``.

For every 4-connected red (2) component, the executable rule records the rows
and columns occupied by that component and paints their Cartesian product green
(3).  For a connected component those occupied row/column sets are contiguous,
so the operation is exactly: recolor and fill that component's bounding box.

The lesson distribution therefore focuses on the distinctions that are
actually identifiable: per-component rather than global filling, recoloring
rather than merely adding green cells, preserving unrelated decorations, and
handling varied component counts, sizes, shapes, and orientations.
"""
from __future__ import annotations

import copy
from collections import deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "699479899861"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "ac41730bf8e3"  # sha256(" ".join(canonical rule.split()))[:12]

SUMMARY = (
    "A zero-background grid contains two to four separated, non-rectangular "
    "red (2) components plus one to three isolated decorative cells. For each "
    "red component independently, recolor and fill its complete bounding box "
    "green (3), preserving every decorative cell."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

INVARIANTS = [
    "background is 0 and color 3 never appears in an input",
    "there are exactly two to four 4-connected red components",
    "every red component is non-rectangular and spans at least two rows and columns",
    "red-component bounding boxes are disjoint, so per-component closure is unambiguous",
    "one to three isolated non-red decorative cells lie outside all red bounding boxes",
    "four consecutive sample indices cover a canonical anchor and varied counts/shapes",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 9..16; canonical scale in the first two schedule roles",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 10..17; canonical scale in the first two schedule roles",
        "valid": "10..17",
    },
    "n_blobs": {
        "type": "int",
        "default": "four-step lesson schedule 2,2,3,4",
        "valid": "2..4",
    },
}

Cell = tuple[int, int]
Shape = frozenset[Cell]
BBox = tuple[int, int, int, int]

_CANONICAL_PROFILES = ((9, 12), (10, 13), (11, 11), (10, 14))
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "small_shape_contrast",
    "three_component_mix",
    "four_component_mix",
)

# Normalized connected templates. Every one has a strict bbox closure:
# bbox area > component cell count.
_L3: Shape = frozenset({(0, 0), (1, 0), (1, 1)})
_L4: Shape = frozenset({(0, 0), (1, 0), (2, 0), (2, 1)})
_T4: Shape = frozenset({(0, 0), (0, 1), (0, 2), (1, 1)})
_Z4: Shape = frozenset({(0, 0), (0, 1), (1, 1), (1, 2)})
_STAIR5: Shape = frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)})
_PLUS5: Shape = frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)})


def _normalize(cells: Iterable[Cell]) -> Shape:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _transform(shape: Shape, index: int) -> Shape:
    cells = set(shape)
    for _ in range(index % 4):
        cells = {(c, -r) for r, c in cells}
    if index >= 4:
        cells = {(r, -c) for r, c in cells}
    return _normalize(cells)


def _variants(shape: Shape) -> tuple[Shape, ...]:
    unique = {_transform(shape, index) for index in range(8)}
    return tuple(sorted(unique, key=lambda s: tuple(sorted(s))))


_SHAPE_FAMILIES = {
    "l3": frozenset(_variants(_L3)),
    "l4": frozenset(_variants(_L4)),
    "t4": frozenset(_variants(_T4)),
    "z4": frozenset(_variants(_Z4)),
    "stair5": frozenset(_variants(_STAIR5)),
    "plus5": frozenset(_variants(_PLUS5)),
}


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _bbox(cells: Iterable[Cell]) -> BBox:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_cells(box: BBox) -> set[Cell]:
    top, left, bottom, right = box
    return {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
    }


def _bbox_overlap(left: BBox, right: BBox) -> bool:
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _components(grid: list[list[int]], color: int = 2) -> list[set[Cell]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[set[Cell]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return sorted(result, key=lambda cells: _bbox(cells))


def _shape_family(cells: Iterable[Cell]) -> str:
    normalized = _normalize(cells)
    for name, variants in _SHAPE_FAMILIES.items():
        if normalized in variants:
            return name
    return "other"


def _analysis(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "components": [], "decorations": []}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"], "components": [], "decorations": []}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "components": [], "decorations": []}
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be within ARC's 1..30 range")
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append("grid values must be integer ARC colors 0..9")
                break
        if errors and errors[-1].startswith("grid values"):
            break
    if any(value == 3 for row in grid for value in row):
        errors.append("input must not contain green (3), the rule's output color")

    components = _components(grid, 2)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 red components, found {len(components)}")

    component_rows = []
    boxes: list[BBox] = []
    for index, cells in enumerate(components):
        box = _bbox(cells)
        boxes.append(box)
        bbox_cells = _bbox_cells(box)
        box_h = box[2] - box[0] + 1
        box_w = box[3] - box[1] + 1
        family = _shape_family(cells)
        if not 3 <= len(cells) <= 5:
            errors.append(f"red component {index} must contain 3..5 cells")
        if box_h < 2 or box_w < 2:
            errors.append(f"red component {index} must span at least two rows and columns")
        if len(cells) >= len(bbox_cells):
            errors.append(f"red component {index} must be a non-rectangular closure witness")
        if family == "other":
            errors.append(f"red component {index} has an unsupported teaching shape")
        component_rows.append(
            {
                "cells": cells,
                "bbox": box,
                "bbox_cells": bbox_cells,
                "bbox_dims": (box_h, box_w),
                "size": len(cells),
                "family": family,
                "added": len(bbox_cells) - len(cells),
            }
        )

    for i, left in enumerate(boxes):
        for right in boxes[i + 1 :]:
            if _bbox_overlap(left, right):
                errors.append("red-component bounding boxes must be disjoint")

    decorations = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2, 3)
    ]
    if not 1 <= len(decorations) <= 3:
        errors.append(f"expected 1..3 decorative cells, found {len(decorations)}")
    occupied = {(r, c) for r, c, _ in decorations}
    red_cells = {cell for component in components for cell in component}
    for r, c, _ in decorations:
        if any((r, c) in _bbox_cells(box) for box in boxes):
            errors.append("decorative cells must lie outside every red bounding box")
        for rr, cc in occupied | red_cells:
            if (rr, cc) == (r, c):
                continue
            if max(abs(rr - r), abs(cc - c)) <= 1:
                errors.append("decorative cells must be isolated from all other foreground cells")
                break

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": component_rows,
        "decorations": decorations,
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked teaching grammar and every canonical input."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Require the exact canonical shape/count/palette profile."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) not in _CANONICAL_PROFILES:
        reasons.append("dimensions are not one of the four canonical profiles")
    if len(analysis["components"]) != 2:
        reasons.append("canonical inputs contain exactly two red components")
    if len(analysis["decorations"]) != 1 or analysis["decorations"][0][2] != 5:
        reasons.append("canonical inputs contain exactly one decorative color-5 cell")
    for component in analysis["components"]:
        if component["family"] != "l4" or component["size"] != 4:
            reasons.append("canonical red components are four-cell L shapes")
            break
        if component["bbox_dims"] not in ((3, 2), (2, 3)):
            reasons.append("canonical red-component boxes are 3x2 or 2x3")
            break
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact non-dimension axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"n_blobs": len(analysis["components"])}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _lesson_defaults(seed: int, sample_index: int) -> dict[str, int]:
    role = sample_index % 4
    if role in (0, 1):
        profile_index = (sample_index // 4 + seed + role) % len(_CANONICAL_PROFILES)
        height, width = _CANONICAL_PROFILES[profile_index]
        return {"grid_h": height, "grid_w": width, "n_blobs": 2}
    return {"n_blobs": (2, 2, 3, 4)[role]}


def _shapes_for_role(role: int, count: int, rng) -> list[Shape]:
    bases = {
        0: (_L4,),
        1: (_L3, _T4),
        2: (_STAIR5, _L4, _Z4),
        3: (_PLUS5, _L3, _Z4, _L4),
    }[role]
    shapes: list[Shape] = []
    for index in range(count):
        base = bases[index % len(bases)]
        shapes.append(rng.choice(_variants(base)))
    return shapes


def _quadrants(height: int, width: int) -> tuple[BBox, BBox, BBox, BBox]:
    middle_row = height // 2
    middle_col = width // 2
    return (
        (0, 0, middle_row - 1, middle_col - 1),
        (0, middle_col + 1, middle_row - 1, width - 1),
        (middle_row + 1, 0, height - 1, middle_col - 1),
        (middle_row + 1, middle_col + 1, height - 1, width - 1),
    )


def _chosen_zones(count: int, rng, height: int, width: int) -> list[BBox]:
    zones = list(_quadrants(height, width))
    if count == 2:
        return [zones[0], zones[3]] if rng.randrange(2) == 0 else [zones[1], zones[2]]
    if count == 3:
        omitted = rng.randrange(4)
        return [zone for index, zone in enumerate(zones) if index != omitted]
    return zones


def _place_shape(grid: list[list[int]], shape: Shape, zone: BBox, rng) -> set[Cell]:
    top, left, bottom, right = zone
    shape_h, shape_w = _shape_dims(shape)
    zone_h = bottom - top + 1
    zone_w = right - left + 1
    if shape_h > zone_h or shape_w > zone_w:
        raise ValueError(
            f"shape {shape_h}x{shape_w} does not fit zone {zone_h}x{zone_w}"
        )
    anchor_top = rng.randint(top, bottom - shape_h + 1)
    anchor_left = rng.randint(left, right - shape_w + 1)
    cells = {(anchor_top + r, anchor_left + c) for r, c in shape}
    for r, c in cells:
        grid[r][c] = 2
    return cells


def _place_decorations(
    grid: list[list[int]],
    count: int,
    red_cells: set[Cell],
    red_boxes: list[BBox],
    rng,
    *,
    canonical_palette: bool,
) -> None:
    height, width = len(grid), len(grid[0])
    palette = [5] if canonical_palette else [1, 4, 5, 6, 7, 8, 9]
    if not canonical_palette:
        rng.shuffle(palette)
    candidates = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(candidates)
    placed: list[Cell] = []
    for r, c in candidates:
        if len(placed) >= count:
            break
        if grid[r][c] != 0:
            continue
        if any((r, c) in _bbox_cells(box) for box in red_boxes):
            continue
        if any(max(abs(rr - r), abs(cc - c)) <= 1 for rr, cc in red_cells | set(placed)):
            continue
        grid[r][c] = palette[len(placed) % len(palette)]
        placed.append((r, c))
    if len(placed) != count:
        raise ValueError(
            f"cannot place {count} isolated decorations in {height}x{width}"
        )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    role = sample_index % 4
    effective_overrides = dict(overrides)
    for axis, value in _lesson_defaults(seed, sample_index).items():
        effective_overrides.setdefault(axis, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int_diff("grid_h", 9, 16)
    width = ctx.draw_int_diff("grid_w", 10, 17)
    n_blobs = ctx.draw_int("n_blobs", 2, 4)
    rng = ctx.draw_rng("layout")

    grid = full_grid(height, width, 0)
    shapes = _shapes_for_role(role, n_blobs, rng)
    zones = _chosen_zones(n_blobs, rng, height, width)
    red_cells: set[Cell] = set()
    red_boxes: list[BBox] = []
    for shape, zone in zip(shapes, zones):
        cells = _place_shape(grid, shape, zone, rng)
        red_cells.update(cells)
        red_boxes.append(_bbox(cells))

    decoration_count = (1, 2, 2, 3)[role]
    _place_decorations(
        grid,
        decoration_count,
        red_cells,
        red_boxes,
        rng,
        canonical_palette=(role in (0, 1)),
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the canonical Racket rule for focused tests."""
    output = copy.deepcopy(grid)
    for component in _components(grid, 2):
        for r, c in _bbox_cells(_bbox(component)):
            output[r][c] = 3
    return output


def _rival_global_red_bbox(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if red:
        for r, c in _bbox_cells(_bbox(red)):
            output[r][c] = 3
    return output


def _rival_first_component_only(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    components = _components(grid, 2)
    if components:
        for r, c in _bbox_cells(_bbox(components[0])):
            output[r][c] = 3
    return output


def _rival_keep_red_add_green(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    for component in _components(grid, 2):
        for r, c in _bbox_cells(_bbox(component)) - component:
            output[r][c] = 3
    return output


def _rival_erase_decorations(grid: list[list[int]]) -> list[list[int]]:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid, 2):
        for r, c in _bbox_cells(_bbox(component)):
            output[r][c] = 3
    return output


def _rival_fixed_canonical_3x2_boxes(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for component in _components(grid, 2):
        top, left, bottom, right = _bbox(component)
        box_h, box_w = bottom - top + 1, right - left + 1
        target_h, target_w = (3, 2) if box_h >= box_w else (2, 3)
        for r in range(top, min(height, top + target_h)):
            for c in range(left, min(width, left + target_w)):
                output[r][c] = 3
    return output


def _witness_multiple_components(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or len(analysis["components"]) < 2:
        return False
    return _rival_global_red_bbox(grid) != rule_mirror(grid)


def _witness_noncanonical_extent(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    return any(
        component["bbox_dims"] not in ((3, 2), (2, 3))
        for component in analysis["components"]
    ) and _rival_fixed_canonical_3x2_boxes(grid) != rule_mirror(grid)


def _witness_decorations_preserved(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and bool(analysis["decorations"])
        and _rival_erase_decorations(grid) != rule_mirror(grid)
    )


def _witness_recolor_original_red(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and all(component["added"] > 0 for component in analysis["components"])
        and _rival_keep_red_add_green(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "canonical_anchor": lambda grid: not strict_canonical_like(grid),
    "separate_components_not_one_global_box": _witness_multiple_components,
    "noncanonical_blob_extent": _witness_noncanonical_extent,
    "decorations_are_preserved": _witness_decorations_preserved,
    "original_red_cells_are_recolored": _witness_recolor_original_red,
}

SEMANTIC_RIVALS = {
    "global_red_bbox": _rival_global_red_bbox,
    "first_component_only": _rival_first_component_only,
    "keep_red_add_green": _rival_keep_red_add_green,
    "erase_decorations": _rival_erase_decorations,
    "fixed_canonical_3x2_boxes": _rival_fixed_canonical_3x2_boxes,
}

WITNESS_RIVALS = {
    "canonical_anchor": ["erase_decorations"],
    "separate_components_not_one_global_box": [
        "global_red_bbox",
        "first_component_only",
    ],
    "noncanonical_blob_extent": ["fixed_canonical_3x2_boxes"],
    "decorations_are_preserved": ["erase_decorations"],
    "original_red_cells_are_recolored": ["keep_red_add_green"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_canonical_3x2_boxes": _rival_fixed_canonical_3x2_boxes,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits every demo but changes the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo but changes the query answer"
                )
    return reasons


def mutation_fixtures():
    """Task-local malformed scenes that the structural checker must reject."""
    fixtures = []

    all_background = full_grid(9, 12, 0)
    fixtures.append(("no_red_components", all_background))

    singleton = full_grid(9, 12, 0)
    singleton[1][1] = 2
    singleton[7][10] = 2
    singleton[4][6] = 5
    fixtures.append(("singleton_red_components", singleton))

    solid_rectangles = full_grid(9, 12, 0)
    for r in range(1, 3):
        for c in range(1, 3):
            solid_rectangles[r][c] = 2
    for r in range(6, 8):
        for c in range(8, 10):
            solid_rectangles[r][c] = 2
    solid_rectangles[4][5] = 5
    fixtures.append(("solid_rectangle_identity", solid_rectangles))

    overlap_boxes = full_grid(9, 12, 0)
    for r, c in ((1, 1), (2, 1), (2, 2)):
        overlap_boxes[r][c] = 2
    for r, c in ((1, 3), (1, 4), (2, 3), (2, 4)):
        overlap_boxes[r][c] = 2
    overlap_boxes[7][10] = 5
    fixtures.append(("touching_components_merge", overlap_boxes))

    green_input = generate(1234, 0)
    green_input[0][0] = 3
    fixtures.append(("output_color_present_in_input", green_input))

    decoration_inside = generate(5678, 1)
    analysis = _analysis(decoration_inside)
    component = analysis["components"][0]
    hole = next(iter(component["bbox_cells"] - component["cells"]))
    decoration_inside[hole[0]][hole[1]] = 5
    fixtures.append(("decoration_inside_red_closure", decoration_inside))

    return fixtures
