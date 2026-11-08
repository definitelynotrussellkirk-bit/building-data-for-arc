def solve(grid):
    """Recolor each nonzero component by its bounding-box nesting depth."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            color = grid[row][col]
            frontier = [(row, col)]
            seen.add((row, col))
            cells = []

            for current_row, current_col in frontier:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    frontier.append((next_row, next_col))

            rows = [cell_row for cell_row, _ in cells]
            cols = [cell_col for _, cell_col in cells]
            components.append(
                {
                    "cells": cells,
                    "box": (min(rows), max(rows), min(cols), max(cols)),
                }
            )

    owner = {
        cell: component_index
        for component_index, component in enumerate(components)
        for cell in component["cells"]
    }
    output = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0:
                continue

            component_index = owner[(row, col)]
            depth = 0
            for other_index, component in enumerate(components):
                if other_index == component_index:
                    continue
                top, bottom, left, right = component["box"]
                if top <= row <= bottom and left <= col <= right:
                    depth += 1
            output[row][col] = 2 + depth

    return output
