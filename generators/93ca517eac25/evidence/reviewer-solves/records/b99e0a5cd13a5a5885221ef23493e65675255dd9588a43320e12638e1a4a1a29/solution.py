"""Visible-only solution for the assigned ARC task.

The two non-background, non-blue colors form a direction cue.  Treat the
smaller color id as the tail and the larger color id as the head.  Recolor the
4-connected blue object whose centroid is farthest in that direction.
"""

from __future__ import annotations

from collections.abc import Sequence


Grid = list[list[int]]
Point = tuple[int, int]


def _components(grid: Sequence[Sequence[int]], color: int) -> list[list[Point]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[Point] = set()
    result: list[list[Point]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue

            component: list[Point] = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current_row + delta_row, current_col + delta_col)
                    neighbor_row, neighbor_col = neighbor
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_col < width
                        and neighbor not in seen
                        and grid[neighbor_row][neighbor_col] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(component)

    return result


def _centroid(points: Sequence[Point]) -> tuple[float, float]:
    return (
        sum(row for row, _ in points) / len(points),
        sum(col for _, col in points) / len(points),
    )


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    cue_colors = sorted({cell for row in grid for cell in row if cell not in (0, 1)})
    if len(cue_colors) != 2:
        return output

    tail_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == cue_colors[0]
    ]
    head_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == cue_colors[1]
    ]
    if not tail_cells or not head_cells:
        return output

    tail_row, tail_col = _centroid(tail_cells)
    head_row, head_col = _centroid(head_cells)
    direction_row = head_row - tail_row
    direction_col = head_col - tail_col

    blue_objects = _components(grid, 1)
    if not blue_objects or (direction_row == 0 and direction_col == 0):
        return output

    def directional_projection(component: Sequence[Point]) -> float:
        center_row, center_col = _centroid(component)
        return center_row * direction_row + center_col * direction_col

    target = max(blue_objects, key=directional_projection)
    for row, col in target:
        output[row][col] = 2
    return output
