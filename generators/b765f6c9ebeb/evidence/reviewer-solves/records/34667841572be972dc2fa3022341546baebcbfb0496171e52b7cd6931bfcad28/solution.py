"""Visible-example solution for the prepared ARC episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Erase one-cell same-color 4-connected components."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen: set[tuple[int, int]] = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            component: list[tuple[int, int]] = []
            frontier = [(start_row, start_col)]
            seen.add((start_row, start_col))

            while frontier:
                row, col = frontier.pop()
                component.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    frontier.append((nr, nc))

            if len(component) > 1:
                for row, col in component:
                    output[row][col] = color

    return output
