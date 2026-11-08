"""Visible-example solution for the prepared fa55db418c9d episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor exact blue L-triomino components by their missing corner."""
    out = [row[:] for row in grid]
    if not grid or not grid[0]:
        return out

    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    missing_corner_color = {
        (1, 1): 2,  # southeast missing
        (1, 0): 3,  # southwest missing
        (0, 1): 4,  # northeast missing
        (0, 0): 8,  # northwest missing
    }

    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == 0:
                continue

            color = grid[row][col]
            component: list[tuple[int, int]] = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    point = (next_row, next_col)
                    if point in seen or grid[next_row][next_col] != color:
                        continue
                    seen.add(point)
                    stack.append(point)

            if color != 1 or len(component) != 3:
                continue

            min_row = min(point[0] for point in component)
            max_row = max(point[0] for point in component)
            min_col = min(point[1] for point in component)
            max_col = max(point[1] for point in component)
            if max_row - min_row != 1 or max_col - min_col != 1:
                continue

            normalized = {
                (point_row - min_row, point_col - min_col)
                for point_row, point_col in component
            }
            missing = {(0, 0), (0, 1), (1, 0), (1, 1)} - normalized
            if len(missing) != 1:
                continue

            replacement = missing_corner_color[next(iter(missing))]
            for point_row, point_col in component:
                out[point_row][point_col] = replacement

    return out
