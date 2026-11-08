"""Visible-example solution for the post-repair reviewer episode."""
from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0] * width for _ in range(height)]
    seen = set()

    for start_row in range(height):
        for start_column in range(width):
            color = grid[start_row][start_column]
            if color == 0 or (start_row, start_column) in seen:
                continue

            queue = deque([(start_row, start_column)])
            seen.add((start_row, start_column))
            cells = []
            while queue:
                row, column = queue.popleft()
                cells.append((row, column))
                for neighbor_row, neighbor_column in (
                    (row - 1, column),
                    (row + 1, column),
                    (row, column - 1),
                    (row, column + 1),
                ):
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_column < width
                        and (neighbor_row, neighbor_column) not in seen
                        and grid[neighbor_row][neighbor_column] == color
                    ):
                        seen.add((neighbor_row, neighbor_column))
                        queue.append((neighbor_row, neighbor_column))

            component_height = max(row for row, _ in cells) - min(row for row, _ in cells) + 1
            component_width = max(column for _, column in cells) - min(column for _, column in cells) + 1
            new_color = 2 if component_width > component_height else 3 if component_height > component_width else 4
            for row, column in cells:
                output[row][column] = new_color

    return output
