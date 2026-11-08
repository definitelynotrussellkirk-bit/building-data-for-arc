"""Semantic generator for ARC task da16b5bf7632.

Find each same-color 4-connected component, crop it, count the enclosed
background regions in that crop, then concatenate the crops left-to-right in
descending hole-count order.  Equal-hole components retain input reading
order.  One blank column separates consecutive crops.
"""
from __future__ import annotations

import copy
from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "da16b5bf7632"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "14cb9ccb4d29"
SUMMARY = (
    "Crop every same-color 4-connected component, sort the crops by enclosed "
    "hole count descending with reading-order ties, and top-align them with "
    "one blank column between adjacent crops."
)
EXAMPLES_NEEDED = 3

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "complete public component profile or a novel lawful profile",
    },
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

INVARIANTS = [
    "background is zero",
    "three to five same-color 4-connected components are separated by zero",
    "at least one component encloses a hole and at least one encloses none",
    "at least two different hole counts make the primary sort observable",
    "equal-hole components preserve bounding-box reading order",
    "normal generalized draws visibly require reordering",
]


def _rectangle_frame(height, width):
    return tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )


def _partition_frame(height, holes):
    """A rectangular frame split into ``holes`` enclosed chambers."""
    width = 2 * holes + 1
    return tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if (
            row in (0, height - 1)
            or col in tuple(range(0, width, 2))
        )
    )


DOT = ((0, 0),)
L_TRIOMINO = ((0, 0), (0, 1), (1, 0))
T_TETROMINO = ((0, 0), (0, 1), (0, 2), (1, 1))
Z_TETROMINO = ((0, 0), (0, 1), (1, 1), (1, 2))
SOLID_2X3 = tuple((row, col) for row in range(2) for col in range(3))
SOLID_3X3 = tuple((row, col) for row in range(3) for col in range(3))
FRAME_3 = _rectangle_frame(3, 3)
FRAME_4 = _rectangle_frame(4, 4)
FRAME_3X4 = _rectangle_frame(3, 4)
FRAME_5X3 = _rectangle_frame(5, 3)
DOUBLE_3X5 = _partition_frame(3, 2)
DOUBLE_4X5 = _partition_frame(4, 2)
TRIPLE_3X7 = _partition_frame(3, 3)

# A component specification is (shape, color-group).  Repeated groups preserve
# the public case where two disconnected singleton objects share one color.
_PUBLIC_PROFILES = (
    ((DOUBLE_3X5, "a"), (FRAME_3, "b"), (L_TRIOMINO, "c")),
    ((FRAME_4, "a"), (FRAME_3, "b"), (DOT, "c"), (DOT, "c")),
    ((DOUBLE_3X5, "a"), (SOLID_3X3, "b"), (FRAME_3, "c")),
    ((FRAME_3, "a"), (DOUBLE_3X5, "b"), (L_TRIOMINO, "c")),
    ((FRAME_4, "a"), (DOUBLE_3X5, "b"), (DOT, "c"), (DOT, "c")),
)

_GENERALIZED_PROFILES = {
    "unique": (
        (DOUBLE_4X5, "a"),
        (FRAME_3X4, "b"),
        (T_TETROMINO, "c"),
    ),
    "tie": (
        (DOUBLE_3X5, "a"),
        (FRAME_4, "b"),
        (FRAME_3X4, "c"),
        (Z_TETROMINO, "d"),
    ),
    "many": (
        (DOUBLE_4X5, "a"),
        (FRAME_3, "b"),
        (T_TETROMINO, "c"),
        (Z_TETROMINO, "d"),
        (DOT, "d"),
    ),
    "exotic": (
        (TRIPLE_3X7, "a"),
        (DOUBLE_4X5, "b"),
        (FRAME_5X3, "c"),
        (SOLID_2X3, "d"),
    ),
}


def _normalize_shape(cells):
    min_row = min(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    return tuple(
        sorted((row - min_row, col - min_col) for row, col in cells)
    )


def _shape_variants(shape):
    variants = {
        _normalize_shape(transformed)
        for transformed in (
            tuple((row, col) for row, col in shape),
            tuple((row, -col) for row, col in shape),
            tuple((-row, col) for row, col in shape),
            tuple((-row, -col) for row, col in shape),
            tuple((col, row) for row, col in shape),
            tuple((col, -row) for row, col in shape),
            tuple((-col, row) for row, col in shape),
            tuple((-col, -row) for row, col in shape),
        )
    }
    return tuple(sorted(variants))


def _shape_key(cells):
    return min(_shape_variants(_normalize_shape(cells)))


def _shape_size(shape):
    return (
        max(row for row, _col in shape) + 1,
        max(col for _row, col in shape) + 1,
    )


def _components(grid):
    """Return same-color 4-connected components in row-major discovery order."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                current_row, current_col = todo.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in (
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1),
                ):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        todo.append((next_row, next_col))
            result.append((color, tuple(sorted(cells))))
    return result


def _hole_count(cells):
    """Count 4-connected background regions enclosed by a component crop."""
    occupied = set(cells)
    min_row = min(row for row, _col in cells)
    max_row = max(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    max_col = max(col for _row, col in cells)
    background = {
        (row, col)
        for row in range(min_row, max_row + 1)
        for col in range(min_col, max_col + 1)
        if (row, col) not in occupied
    }
    seen = set()
    holes = 0
    for start in sorted(background):
        if start in seen:
            continue
        todo = [start]
        seen.add(start)
        touches_crop_edge = False
        while todo:
            row, col = todo.pop()
            touches_crop_edge |= (
                row in (min_row, max_row) or col in (min_col, max_col)
            )
            for delta_row, delta_col in (
                (1, 0),
                (-1, 0),
                (0, 1),
                (0, -1),
            ):
                neighbor = (row + delta_row, col + delta_col)
                if neighbor in background and neighbor not in seen:
                    seen.add(neighbor)
                    todo.append(neighbor)
        if not touches_crop_edge:
            holes += 1
    return holes


def _component_record(color, cells):
    min_row = min(row for row, _col in cells)
    max_row = max(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    max_col = max(col for _row, col in cells)
    return {
        "color": color,
        "cells": cells,
        "bbox": (min_row, min_col, max_row, max_col),
        "holes": _hole_count(cells),
        "shape_key": _shape_key(cells),
    }


def _profile_signature(records):
    return tuple(
        sorted((record["holes"], record["shape_key"]) for record in records)
    )


def _profile_signature_from_specs(specs):
    records = [
        _component_record(index + 1, _normalize_shape(shape))
        for index, (shape, _group) in enumerate(specs)
    ]
    return _profile_signature(records)


_PUBLIC_PROFILE_SIGNATURES = tuple(
    dict.fromkeys(_profile_signature_from_specs(specs) for specs in _PUBLIC_PROFILES)
)


def _crop_component(record):
    min_row, min_col, max_row, max_col = record["bbox"]
    crop = full_grid(max_row - min_row + 1, max_col - min_col + 1, 0)
    for row, col in record["cells"]:
        crop[row - min_row][col - min_col] = record["color"]
    return crop


def _rule_output(records):
    ordered = sorted(
        records,
        key=lambda record: (
            -record["holes"],
            record["bbox"][0],
            record["bbox"][1],
        ),
    )
    crops = [_crop_component(record) for record in ordered]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = full_grid(height, width, 0)
    left = 0
    for crop in crops:
        for row, values in enumerate(crop):
            for col, value in enumerate(values):
                if value != 0:
                    output[row][left + col] = value
        left += len(crop[0]) + 1
    return output


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if not 8 <= height <= 24 or not 12 <= width <= 30:
        errors.append("grid dimensions must be height 8..24 and width 12..30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    if errors:
        return {"errors": errors, "facts": None}

    records = [
        _component_record(color, cells)
        for color, cells in _components(grid)
    ]
    if not 3 <= len(records) <= 5:
        errors.append(
            f"expected three to five same-color components, found {len(records)}"
        )
    holes = [record["holes"] for record in records]
    if any(holes_count > 3 for holes_count in holes):
        errors.append("components may enclose at most three holes")
    if not any(holes_count > 0 for holes_count in holes):
        errors.append("at least one component must enclose a hole")
    if 0 not in holes:
        errors.append("at least one component must enclose no holes")
    if len(set(holes)) < 2:
        errors.append("at least two hole-count ranks are required")

    signature = _profile_signature(records) if records else ()
    linked_index = next(
        (
            index
            for index, public_signature in enumerate(_PUBLIC_PROFILE_SIGNATURES)
            if signature == public_signature
        ),
        None,
    )
    if (
        records
        and holes == sorted(holes, reverse=True)
        and linked_index is None
    ):
        errors.append(
            "generalized scenes must visibly require hole-count reordering"
        )

    facts = None
    if not errors:
        counts = Counter(holes)
        facts = {
            "height": height,
            "width": width,
            "component_count": len(records),
            "colors": tuple(record["color"] for record in records),
            "hole_sequence": tuple(holes),
            "hole_histogram": tuple(sorted(counts.items())),
            "has_tie": any(count >= 2 for count in counts.values()),
            "same_color_disconnected": (
                len({record["color"] for record in records}) < len(records)
            ),
            "linked_index": linked_index,
            "scene_family": (
                "linked" if linked_index is not None else "generalized"
            ),
            "records": records,
            "output": _rule_output(records),
        }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["scene_family"]}


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    if facts["linked_index"] is not None:
        return f"public_topology_{facts['linked_index'] + 1}"
    holes = "-".join(str(value) for value in facts["hole_sequence"])
    return (
        f"generalized:{facts['component_count']}components:"
        f"reading_holes={holes}"
    )


def rule_mirror(grid):
    """Input-pure Python mirror used only for focused parity evidence."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["output"])


def _choose_unsorted_order(rng, specs):
    """Choose reading order with a strict hole-count inversion."""
    specs = list(specs)
    holes_by_shape = {
        _shape_key(shape): _hole_count(_normalize_shape(shape))
        for shape, _group in specs
    }
    for _ in range(100):
        rng.shuffle(specs)
        hole_sequence = [holes_by_shape[_shape_key(shape)] for shape, _ in specs]
        if hole_sequence != sorted(hole_sequence, reverse=True):
            return tuple(specs)
    raise RuntimeError("could not construct a visible hole-sort inversion")


def _feasible_row_partitions(shapes, height, width):
    """Return ordered row partitions with one blank row/column of separation."""
    count = len(shapes)
    sizes = [_shape_size(shape) for shape in shapes]
    candidates = []

    def visit(start, groups):
        if start == count:
            row_heights = [
                max(sizes[index][0] for index in group)
                for group in groups
            ]
            total_height = sum(row_heights) + len(groups) - 1
            if total_height > height - 2:
                return
            for group in groups:
                total_width = (
                    sum(sizes[index][1] for index in group) + len(group) - 1
                )
                if total_width > width - 2:
                    return
            candidates.append(tuple(tuple(group) for group in groups))
            return
        for group_size in range(1, min(3, count - start) + 1):
            visit(
                start + group_size,
                groups + [tuple(range(start, start + group_size))],
            )

    visit(0, [])
    return candidates


def _pack_specs(rng, specs, height, width):
    """Orient, color, and place specs while preserving requested read order."""
    for _ in range(200):
        oriented = [
            rng.choice(_shape_variants(shape))
            for shape, _group in specs
        ]
        partitions = _feasible_row_partitions(oriented, height, width)
        if not partitions:
            continue
        partition = rng.choice(partitions)
        row_heights = [
            max(_shape_size(oriented[index])[0] for index in group)
            for group in partition
        ]
        total_height = sum(row_heights) + len(partition) - 1
        top = rng.randint(0, height - total_height)
        positions = [None] * len(specs)
        current_top = top
        for group, row_height in zip(partition, row_heights):
            widths = [_shape_size(oriented[index])[1] for index in group]
            total_width = sum(widths) + len(group) - 1
            left = rng.randint(0, width - total_width)
            for index, shape_width in zip(group, widths):
                positions[index] = (current_top, left)
                left += shape_width + 1
            current_top += row_height + 1

        groups = tuple(dict.fromkeys(group for _shape, group in specs))
        palette = rng.sample(range(1, 10), len(groups))
        color_by_group = dict(zip(groups, palette))
        grid = full_grid(height, width, 0)
        for (shape, group), cells, (base_row, base_col) in zip(
            specs, oriented, positions
        ):
            del shape
            color = color_by_group[group]
            for row, col in cells:
                grid[base_row + row][base_col + col] = color
        return grid
    raise RuntimeError("could not orient and pack component profile")


def _build_linked(rng, band):
    choices = {
        "easy": (0, 2, 3, 0, 2, 1, 4),
        "medium": (0, 1, 2, 3, 4),
        "hard": (1, 4, 0, 2, 3, 4),
    }[band]
    specs = _PUBLIC_PROFILES[rng.choice(choices)]
    ordered = _choose_unsorted_order(rng, specs)
    height, width = {
        "easy": (12, 18),
        "medium": (13, 19),
        "hard": (14, 20),
    }[band]
    return _pack_specs(rng, ordered, height, width)


def _build_generalized(rng, band):
    choices = {
        "easy": ("unique", "tie", "unique", "tie"),
        "medium": ("unique", "tie", "many", "exotic"),
        "hard": ("tie", "many", "exotic", "many", "exotic"),
    }[band]
    specs = _GENERALIZED_PROFILES[rng.choice(choices)]
    ordered = _choose_unsorted_order(rng, specs)
    height, width = {
        "easy": (12, 18),
        "medium": (14, 20),
        "hard": (16, 22),
    }[band]
    return _pack_specs(rng, ordered, height, width)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = context.draw_choice("scene_family", SCENE_FAMILIES)
    rng = context.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        _build_linked(rng, band)
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["scene_family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['scene_family']}"
                ]
            )
        )
    return grid
