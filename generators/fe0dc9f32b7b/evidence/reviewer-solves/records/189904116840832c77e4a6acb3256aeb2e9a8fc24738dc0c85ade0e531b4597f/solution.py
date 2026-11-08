"""Visible-example solution for the blind ARC task."""

from __future__ import annotations

from collections.abc import Sequence

Grid = list[list[int]]
Point = tuple[int, int]
BBox = tuple[int, int, int, int]


def _bounded_zero_components(grid: Sequence[Sequence[int]]) -> list[dict[str, object]]:
    """Return four-connected zero regions that do not touch the grid boundary."""
    height = len(grid)
    width = len(grid[0])
    seen: set[Point] = set()
    components: list[dict[str, object]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            points: list[Point] = []
            touches_boundary = False

            while stack:
                current_row, current_col = stack.pop()
                points.append((current_row, current_col))
                if (
                    current_row == 0
                    or current_row == height - 1
                    or current_col == 0
                    or current_col == width - 1
                ):
                    touches_boundary = True

                for row_delta, col_delta in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (current_row + row_delta, current_col + col_delta)
                    neighbor_row, neighbor_col = neighbor
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_col < width
                        and grid[neighbor_row][neighbor_col] == 0
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)

            if not touches_boundary:
                rows = [point[0] for point in points]
                cols = [point[1] for point in points]
                components.append(
                    {
                        "points": points,
                        "bbox": (min(rows), min(cols), max(rows), max(cols)),
                        "parent": None,
                        "children": [],
                        "color_index": 0,
                    }
                )

    return components


def _strictly_contains(outer: BBox, inner: BBox) -> bool:
    return (
        outer[0] < inner[0]
        and outer[1] < inner[1]
        and outer[2] > inner[2]
        and outer[3] > inner[3]
    )


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Color the nested background-region tree using the left-hand color key.

    A uniquely nested child advances to the next key color.  When a region has
    several sibling children, those branches inherit the current key color.
    Regions deeper than the supplied key stay zero.
    """
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    output = [list(row) for row in grid]
    palette = [row[0] for row in grid if row[0] not in (0, 8)]
    components = _bounded_zero_components(grid)

    # Bounding boxes reveal the visible nesting relation in every demonstration.
    for child_index, child in enumerate(components):
        child_box = child["bbox"]
        assert isinstance(child_box, tuple)
        possible_parents: list[tuple[int, int]] = []
        for parent_index, parent in enumerate(components):
            if parent_index == child_index:
                continue
            parent_box = parent["bbox"]
            assert isinstance(parent_box, tuple)
            if _strictly_contains(parent_box, child_box):
                box_area = (parent_box[2] - parent_box[0] + 1) * (
                    parent_box[3] - parent_box[1] + 1
                )
                possible_parents.append((box_area, parent_index))

        if possible_parents:
            _, parent_index = min(possible_parents)
            child["parent"] = parent_index
            parent_children = components[parent_index]["children"]
            assert isinstance(parent_children, list)
            parent_children.append(child_index)

    stack: list[tuple[int, int]] = [
        (index, 0)
        for index, component in enumerate(components)
        if component["parent"] is None
    ]
    while stack:
        component_index, color_index = stack.pop()
        component = components[component_index]
        component["color_index"] = color_index
        children = component["children"]
        assert isinstance(children, list)
        next_index = color_index + 1 if len(children) == 1 else color_index
        stack.extend((child_index, next_index) for child_index in children)

    for component in components:
        color_index = component["color_index"]
        points = component["points"]
        assert isinstance(color_index, int)
        assert isinstance(points, list)
        if color_index >= len(palette):
            continue
        color = palette[color_index]
        for row, col in points:
            output[row][col] = color

    return output
