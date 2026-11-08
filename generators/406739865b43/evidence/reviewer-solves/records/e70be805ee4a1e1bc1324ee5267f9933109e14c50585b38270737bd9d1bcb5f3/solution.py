"""Visible-example solution for ARC task 406739865b43."""
from __future__ import annotations

from collections import deque


def solve(grid):
    """Crop the body component whose color is named by the row-0 marker."""
    marker_colors = [value for value in grid[0] if value != 0]
    if not marker_colors:
        raise ValueError("row 0 contains no marker color")
    marker_color = marker_colors[0]

    height = len(grid)
    width = len(grid[0])
    seen = set()
    matching_components = []
    for row in range(1, height):
        for col in range(width):
            if grid[row][col] != marker_color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    next_cell = (next_row, next_col)
                    if (
                        1 <= next_row < height
                        and 0 <= next_col < width
                        and next_cell not in seen
                        and grid[next_row][next_col] == marker_color
                    ):
                        seen.add(next_cell)
                        queue.append(next_cell)
            matching_components.append(cells)

    if not matching_components:
        raise ValueError("no body component has the marker color")
    cells = min(
        matching_components,
        key=lambda component: (
            min(row for row, _ in component),
            min(col for _, col in component),
        ),
    )
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]
