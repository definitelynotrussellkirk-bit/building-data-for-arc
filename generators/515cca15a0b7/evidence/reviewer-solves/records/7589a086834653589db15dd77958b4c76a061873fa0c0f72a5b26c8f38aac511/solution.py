"""Visible-example solution for the post-repair episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            component = []
            touches_horizontal = False
            touches_vertical = False

            while stack:
                row, col = stack.pop()
                component.append((row, col))
                touches_horizontal |= row == 0 or row == height - 1
                touches_vertical |= col == 0 or col == width - 1

                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = row + delta_row
                    next_col = col + delta_col
                    point = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and point not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(point)
                        stack.append(point)

            if touches_horizontal and touches_vertical:
                for row, col in component:
                    output[row][col] = color

    return output
