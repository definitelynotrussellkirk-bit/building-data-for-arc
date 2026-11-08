from math import atan2


def _components_of_color(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == color
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            components.append(component)

    return components


def _find_payload_boxes(grid):
    boxes = []
    for component in _components_of_color(grid, 2):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top < 2 or right - left < 2:
            continue

        perimeter = {
            *((top, col) for col in range(left, right + 1)),
            *((bottom, col) for col in range(left, right + 1)),
            *((row, left) for row in range(top, bottom + 1)),
            *((row, right) for row in range(top, bottom + 1)),
        }
        if not perimeter.issubset(set(component)):
            continue

        payload_cells = [
            (row, col)
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if grid[row][col] not in (0, 1, 2)
        ]
        payload_colors = {grid[row][col] for row, col in payload_cells}
        if len(payload_colors) != 1:
            continue

        boxes.append(
            {
                "center": ((top + bottom) / 2, (left + right) / 2),
                "cells": payload_cells,
                "color": next(iter(payload_colors)),
            }
        )

    return boxes


def solve(grid):
    output = [row[:] for row in grid]
    boxes = _find_payload_boxes(grid)
    if len(boxes) < 2:
        return output

    center_row = sum(box["center"][0] for box in boxes) / len(boxes)
    center_col = sum(box["center"][1] for box in boxes) / len(boxes)
    boxes.sort(
        key=lambda box: atan2(
            box["center"][0] - center_row,
            box["center"][1] - center_col,
        )
    )

    source_colors = [box["color"] for box in boxes]
    for index, box in enumerate(boxes):
        replacement = source_colors[(index + 1) % len(boxes)]
        for row, col in box["cells"]:
            output[row][col] = replacement

    return output
