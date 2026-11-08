from collections import Counter, deque


def _components(grid, background):
    """Return monochromatic 4-connected non-background components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            min_row = min(row for row, _ in cells)
            max_row = max(row for row, _ in cells)
            min_col = min(col for _, col in cells)
            max_col = max(col for _, col in cells)
            components.append(
                {
                    "color": color,
                    "cells": set(cells),
                    "bounds": (min_row, max_row, min_col, max_col),
                }
            )

    return components


def _is_hollow_frame(component):
    min_row, max_row, min_col, max_col = component["bounds"]
    height = max_row - min_row + 1
    width = max_col - min_col + 1
    if height < 3 or width < 3:
        return False

    border = {
        (row, col)
        for row in range(min_row, max_row + 1)
        for col in range(min_col, max_col + 1)
        if row in (min_row, max_row) or col in (min_col, max_col)
    }
    return component["cells"] == border


def solve(grid):
    """Move ranked loose objects into ranked hollow frames, centered unchanged."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    components = _components(grid, background)
    frames = [component for component in components if _is_hollow_frame(component)]
    objects = [component for component in components if not _is_hollow_frame(component)]

    def frame_key(component):
        min_row, max_row, min_col, max_col = component["bounds"]
        inner_height = max_row - min_row - 1
        inner_width = max_col - min_col - 1
        return (inner_height * inner_width, inner_height, inner_width, min_row, min_col)

    def object_key(component):
        min_row, max_row, min_col, max_col = component["bounds"]
        return (
            len(component["cells"]),
            (max_row - min_row + 1) * (max_col - min_col + 1),
            max_row - min_row + 1,
            max_col - min_col + 1,
            min_row,
            min_col,
        )

    frames.sort(key=frame_key)
    objects.sort(key=object_key)

    result = [row[:] for row in grid]
    for component in objects:
        for row, col in component["cells"]:
            result[row][col] = background

    for frame, component in zip(frames, objects):
        frame_min_row, frame_max_row, frame_min_col, frame_max_col = frame["bounds"]
        object_min_row, object_max_row, object_min_col, object_max_col = component["bounds"]

        inner_height = frame_max_row - frame_min_row - 1
        inner_width = frame_max_col - frame_min_col - 1
        object_height = object_max_row - object_min_row + 1
        object_width = object_max_col - object_min_col + 1

        top = frame_min_row + 1 + (inner_height - object_height) // 2
        left = frame_min_col + 1 + (inner_width - object_width) // 2

        for row, col in component["cells"]:
            destination_row = top + row - object_min_row
            destination_col = left + col - object_min_col
            result[destination_row][destination_col] = component["color"]

    return result
