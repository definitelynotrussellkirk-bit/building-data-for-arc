from collections import deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = set()
            while queue:
                current_row, current_col = queue.popleft()
                cells.add((current_row, current_col))
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
                        queue.append((next_row, next_col))

            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "top": min(rows),
                    "left": min(cols),
                    "bottom": max(rows),
                    "right": max(cols),
                }
            )
    return result


def _height(component):
    return component["bottom"] - component["top"] + 1


def _width(component):
    return component["right"] - component["left"] + 1


def _is_complete_frame(component):
    if _height(component) < 3 or _width(component) < 3:
        return False
    expected = {
        (row, col)
        for row in range(component["top"], component["bottom"] + 1)
        for col in range(component["left"], component["right"] + 1)
        if row in (component["top"], component["bottom"])
        or col in (component["left"], component["right"])
    }
    return component["cells"] == expected


def _is_solid_rectangle(component):
    return len(component["cells"]) == _height(component) * _width(component)


def solve(grid):
    """Move each solid colored rectangle into the matching complete gray frame."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]

    frames = [component for component in _components(grid, 8) if _is_complete_frame(component)]

    colors = sorted({value for row in grid for value in row} - {0, 8})
    pieces = []
    for color in colors:
        pieces.extend(
            component
            for component in _components(grid, color)
            if _is_solid_rectangle(component)
        )

    unused = set(range(len(pieces)))
    for frame in frames:
        for row, col in frame["cells"]:
            output[row][col] = 8

        interior_height = _height(frame) - 2
        interior_width = _width(frame) - 2
        match = next(
            (
                index
                for index in sorted(unused)
                if _height(pieces[index]) == interior_height
                and _width(pieces[index]) == interior_width
            ),
            None,
        )
        if match is None:
            continue

        unused.remove(match)
        fill_color = pieces[match]["color"]
        for row in range(frame["top"] + 1, frame["bottom"]):
            for col in range(frame["left"] + 1, frame["right"]):
                output[row][col] = fill_color

    return output
