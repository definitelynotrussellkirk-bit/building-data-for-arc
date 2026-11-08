from collections import Counter, deque


def solve(grid):
    """Move repeated-color corner objects one object-width inward diagonally."""
    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            cells = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "min_row": min(rows),
                    "max_row": max(rows),
                    "min_col": min(cols),
                    "max_col": max(cols),
                }
            )

    component_count_by_color = Counter(component["color"] for component in components)
    moving = [
        component
        for component in components
        if component_count_by_color[component["color"]] > 1
    ]

    result = [row[:] for row in grid]
    for component in moving:
        for row, col in component["cells"]:
            result[row][col] = background

    for component in moving:
        box_height = component["max_row"] - component["min_row"] + 1
        box_width = component["max_col"] - component["min_col"] + 1

        if component["min_row"] == 0:
            row_shift = box_height
        elif component["max_row"] == height - 1:
            row_shift = -box_height
        else:
            row_shift = 0

        if component["min_col"] == 0:
            col_shift = box_width
        elif component["max_col"] == width - 1:
            col_shift = -box_width
        else:
            col_shift = 0

        for row, col in component["cells"]:
            result[row + row_shift][col + col_shift] = component["color"]

    return result
