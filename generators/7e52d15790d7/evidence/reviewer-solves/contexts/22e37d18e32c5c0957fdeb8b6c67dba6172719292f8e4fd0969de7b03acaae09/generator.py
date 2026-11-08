"""Generator for 7e52d15790d7 — sort by true perimeter and pack.

Find the three isolated nonzero 4-connected components. Compute each
component's true 4-neighbor edge perimeter, sort descending, crop each
component to its bounding box, and pack the crops left-to-right with one
zero column between adjacent crops.

The three-sample schedule deliberately contains (1) a bbox-perimeter tie
whose true perimeters differ, (2) an area/perimeter ranking inversion, and
(3) a canonical-like varied-shape scene. Every scheduled input order differs
from the required descending-perimeter output order.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e52d15790d7"
TASK_ID = "7e52d15790d7"
VERSION = "3.0.0"
RULE_HASH = "50de31dd583a"

SUMMARY = (
    "Three isolated, distinct-color components have true 4-neighbor edge "
    "perimeters 12, 10, and 8. Sort the components by that perimeter in "
    "descending order, crop each to its bounding box, and gallery-pack the "
    "crops left-to-right with one zero column between them. The scheduled "
    "shape families explicitly distinguish true perimeter from bbox "
    "perimeter, area, and input position."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly three isolated 4-connected nonzero components",
    "each component is single-color and the three colors are distinct",
    "the true 4-neighbor perimeters are exactly 12, 10, and 8",
    "the ordinary three-demo schedule refutes bbox, area, and position order",
]

SHAPE_PROFILES = (
    "bbox_tie",
    "area_inversion",
    "canonical_varied",
)
INPUT_ORDERS = (
    "10_8_12",
    "8_12_10",
    "12_8_10",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed rng 9..14",
        "valid": "9..14",
        "doc": "Exact returned input height; spans all canonical heights.",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed rng 12..18",
        "valid": "12..18",
        "doc": "Exact returned input width; spans all canonical widths.",
    },
    "shape_profile": {
        "type": "str",
        "default": "three-sample semantic schedule",
        "valid": "|".join(SHAPE_PROFILES),
        "doc": (
            "Linked set of perimeter-12/10/8 shapes. bbox_tie refutes bbox "
            "perimeter; area_inversion refutes area; canonical_varied "
            "supplies the ordinary canonical-like branch."
        ),
    },
    "input_order": {
        "type": "str",
        "default": "three-sample non-sorted schedule",
        "valid": "|".join(INPUT_ORDERS),
        "doc": "Exact left-to-right sequence of true component perimeters.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Shapes are normalized cell sets keyed by their true edge perimeter.
_PROFILE_SHAPES = {
    # p12 and p10 both occupy a 3x2 bbox (bbox perimeter 10), have the
    # same area (5), yet have different true edge perimeters.
    "bbox_tie": {
        12: ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
        10: ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        8: ((0, 0), (1, 0), (1, 1)),
    },
    # The six-cell rectangle has lower perimeter than the five-cell plus,
    # so sorting by area gives a different answer.
    "area_inversion": {
        12: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        10: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        8: ((0, 0), (0, 1), (1, 0), (1, 1)),
    },
    "canonical_varied": {
        12: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        10: ((0, 0), (0, 1), (0, 2), (1, 1)),
        8: ((0, 0), (0, 1), (0, 2)),
    },
}

_PROFILE_SIGNATURES = {
    # (true perimeter, cell count, bbox perimeter), descending true perimeter
    "bbox_tie": ((12, 5, 10), (10, 5, 10), (8, 3, 8)),
    "area_inversion": ((12, 5, 12), (10, 6, 10), (8, 4, 8)),
    "canonical_varied": ((12, 5, 12), (10, 4, 10), (8, 3, 8)),
}

_ORDER_VALUES = {
    name: tuple(int(value) for value in name.split("_"))
    for name in INPUT_ORDERS
}


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row: list[int] = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    return (None, errors) if errors else (converted, [])


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform(
    cells: Iterable[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    transformed = _normalize(cells)
    if code >= 4:
        transformed = _normalize((row, -col) for row, col in transformed)
    for _ in range(code % 4):
        transformed = _normalize((col, -row) for row, col in transformed)
    return transformed


def _components_nonzero(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = row + drow, col + dcol
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] != 0
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            components.append(cells)
    return components


def _perimeter(cells: Iterable[tuple[int, int]]) -> int:
    cell_set = set(cells)
    return sum(
        (row + drow, col + dcol) not in cell_set
        for row, col in cell_set
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_perimeter(cells: Iterable[tuple[int, int]]) -> int:
    row0, col0, row1, col1 = _bbox(cells)
    return 2 * ((row1 - row0 + 1) + (col1 - col0 + 1))


def _crop(
    grid: list[list[int]], cells: Iterable[tuple[int, int]]
) -> list[list[int]]:
    cells = tuple(cells)
    cell_set = set(cells)
    row0, col0, row1, col1 = _bbox(cells)
    return [
        [
            grid[row][col] if (row, col) in cell_set else 0
            for col in range(col0, col1 + 1)
        ]
        for row in range(row0, row1 + 1)
    ]


def _analysis(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if converted is None:
        return result

    components = _components_nonzero(converted)
    records: list[dict[str, Any]] = []
    for cells in components:
        row0, col0, row1, col1 = _bbox(cells)
        colors = {converted[row][col] for row, col in cells}
        records.append(
            {
                "cells": tuple(sorted(cells)),
                "colors": tuple(sorted(colors)),
                "size": len(cells),
                "perimeter": _perimeter(cells),
                "bbox_perimeter": 2 * (
                    (row1 - row0 + 1) + (col1 - col0 + 1)
                ),
                "bbox": (row0, col0, row1, col1),
            }
        )

    if len(components) != 3:
        errors.append(f"expected exactly 3 nonzero components, found {len(components)}")
    for index, record in enumerate(records):
        if len(record["colors"]) != 1:
            errors.append(
                f"component {index} must be single-color, found {record['colors']}"
            )
        if not 3 <= record["size"] <= 6:
            errors.append(
                f"component {index} size {record['size']} outside required 3..6"
            )
    component_colors = [record["colors"][0] for record in records if len(record["colors"]) == 1]
    if len(component_colors) == 3 and len(set(component_colors)) != 3:
        errors.append("the three component colors must be distinct")

    perimeters = sorted((record["perimeter"] for record in records), reverse=True)
    if len(records) == 3 and perimeters != [12, 10, 8]:
        errors.append(
            f"true component perimeters must be [12, 10, 8], found {perimeters}"
        )

    true_sorted = sorted(
        records,
        key=lambda record: (
            -record["perimeter"],
            record["bbox"][0],
            record["bbox"][1],
        ),
    )
    left_sorted = sorted(records, key=lambda record: record["bbox"][1])
    bbox_sorted = sorted(
        records,
        key=lambda record: (
            -record["bbox_perimeter"],
            record["bbox"][0],
            record["bbox"][1],
        ),
    )
    area_sorted = sorted(
        records,
        key=lambda record: (
            -record["size"],
            record["bbox"][0],
            record["bbox"][1],
        ),
    )

    signature = tuple(
        (record["perimeter"], record["size"], record["bbox_perimeter"])
        for record in true_sorted
    )
    profile = next(
        (
            name
            for name, expected in _PROFILE_SIGNATURES.items()
            if signature == expected
        ),
        None,
    )
    left_perimeters = tuple(record["perimeter"] for record in left_sorted)
    input_order = next(
        (
            name
            for name, expected in _ORDER_VALUES.items()
            if left_perimeters == expected
        ),
        None,
    )

    output: list[list[int]] | None = None
    if records:
        crops = [_crop(converted, record["cells"]) for record in true_sorted]
        output_height = max(len(crop) for crop in crops)
        output_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
        output = full_grid(output_height, output_width, 0)
        left = 0
        for crop in crops:
            for row_index, row in enumerate(crop):
                for col_index, value in enumerate(row):
                    if value != 0:
                        output[row_index][left + col_index] = value
            left += len(crop[0]) + 1

    result.update(
        {
            "grid": converted,
            "components": records,
            "perimeters_desc": tuple(record["perimeter"] for record in true_sorted),
            "left_to_right_perimeters": left_perimeters,
            "bbox_order_perimeters": tuple(record["perimeter"] for record in bbox_sorted),
            "area_order_perimeters": tuple(record["perimeter"] for record in area_sorted),
            "shape_profile": profile,
            "input_order": input_order,
            "sort_changes_left_to_right": left_perimeters != (12, 10, 8),
            "bbox_sort_disagrees": tuple(record["perimeter"] for record in bbox_sorted) != (12, 10, 8),
            "area_sort_disagrees": tuple(record["perimeter"] for record in area_sorted) != (12, 10, 8),
            "output": output,
            "errors": errors,
        }
    )
    return result


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["shape_profile"] is None:
        raise ValueError("grid does not match a declared generated shape profile")
    if analysis["input_order"] is None:
        raise ValueError("grid does not match a declared generated input order")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_profile": analysis["shape_profile"],
        "input_order": analysis["input_order"],
        "perimeters_desc": analysis["perimeters_desc"],
        "left_to_right_perimeters": analysis["left_to_right_perimeters"],
        "bbox_order_perimeters": analysis["bbox_order_perimeters"],
        "area_order_perimeters": analysis["area_order_perimeters"],
        "sort_changes_left_to_right": analysis["sort_changes_left_to_right"],
        "bbox_sort_disagrees": analysis["bbox_sort_disagrees"],
        "area_sort_disagrees": analysis["area_sort_disagrees"],
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def self_check(
    grid: Any, *, difficulty: Any = None, meta: Any = None
) -> list[str]:
    """Check the structural input grammar shared by generated and public grids."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def _scheduled_choice(ctx, label: str, values: tuple[str, ...], sample_index: int) -> str:
    # Ordinary sequential episodes see a complete three-example semantic
    # schedule. Explicit overrides retain the full documented domain.
    options = values if label in ctx.overrides else (values[sample_index % len(values)],)
    return ctx.draw_choice(label, options)


def _random_composition(total: int, parts: int, rng) -> list[int]:
    values = [0] * parts
    for _ in range(total):
        values[rng.randrange(parts)] += 1
    return values


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = ctx.draw_int("grid_h", 9, 14)
    width = ctx.draw_int("grid_w", 12, 18)
    shape_profile = _scheduled_choice(
        ctx, "shape_profile", SHAPE_PROFILES, sample_index
    )
    input_order = _scheduled_choice(
        ctx, "input_order", INPUT_ORDERS, sample_index
    )
    colors = ctx.draw_distinct_colors("component_colors", n=3, exclude=(0,))
    rng = ctx.draw_rng(f"layout:{band}")

    shapes_by_perimeter = {
        perimeter: _transform(cells, rng.randrange(8))
        for perimeter, cells in _PROFILE_SHAPES[shape_profile].items()
    }
    color_by_perimeter = {
        perimeter: color
        for perimeter, color in zip((12, 10, 8), colors)
    }
    position_perimeters = _ORDER_VALUES[input_order]
    position_shapes = [
        shapes_by_perimeter[perimeter]
        for perimeter in position_perimeters
    ]
    shape_widths = [max(col for _row, col in shape) + 1 for shape in position_shapes]
    shape_heights = [max(row for row, _col in shape) + 1 for shape in position_shapes]

    mandatory_width = sum(shape_widths) + 2
    if mandatory_width > width:
        raise ValueError(
            f"grid_w={width} cannot fit selected profile width {mandatory_width}"
        )
    left_margin, extra_gap_1, extra_gap_2, _right_margin = _random_composition(
        width - mandatory_width, 4, rng
    )
    lefts = [left_margin]
    lefts.append(lefts[0] + shape_widths[0] + 1 + extra_gap_1)
    lefts.append(lefts[1] + shape_widths[1] + 1 + extra_gap_2)

    if shape_profile == "bbox_tie":
        # The p12 and p10 bboxes tie. A shared top row makes the Racket
        # row/column tie-break follow left-to-right input order, where p10
        # deliberately precedes p12, so bbox sorting cannot mimic the answer.
        common_top = rng.randint(0, height - max(shape_heights))
        tops = [common_top] * 3
    else:
        tops = [
            rng.randint(0, height - shape_height)
            for shape_height in shape_heights
        ]

    grid = full_grid(height, width, 0)
    for perimeter, shape, top, left in zip(
        position_perimeters, position_shapes, tops, lefts
    ):
        color = color_by_perimeter[perimeter]
        for row, col in shape:
            grid[top + row][left + col] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed["shape_profile"] != shape_profile:
        raise AssertionError(
            f"shape profile drift: requested {shape_profile}, observed {observed['shape_profile']}"
        )
    if observed["input_order"] != input_order:
        raise AssertionError(
            f"input order drift: requested {input_order}, observed {observed['input_order']}"
        )
    return grid
