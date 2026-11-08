"""Visible-example solution for ARC task 6d095613d305."""
from __future__ import annotations


def _inclusive_steps(start: int, end: int):
    """Yield coordinates after start through end, in either direction."""
    if start == end:
        return range(0)
    step = 1 if end > start else -1
    return range(start + step, end + step, step)


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0]) if height else 0

    points_by_color: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                points_by_color.setdefault(color, []).append((row_index, column_index))

    paths: dict[int, set[tuple[int, int]]] = {}
    for color, points in points_by_color.items():
        ordered = sorted(points)  # row-major order
        occupied: set[tuple[int, int]] = set()
        if ordered:
            occupied.add(ordered[0])
        for (row_1, column_1), (row_2, column_2) in zip(ordered, ordered[1:]):
            # Horizontal first, on the earlier marker's row.
            occupied.update(
                (row_1, column)
                for column in _inclusive_steps(column_1, column_2)
            )
            # Then vertical, on the later marker's column.
            occupied.update(
                (row, column_2)
                for row in _inclusive_steps(row_1, row_2)
            )
        paths[color] = occupied

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for column in range(width):
            users = [color for color, path in paths.items() if (row, column) in path]
            if len(users) == 1:
                output[row][column] = users[0]
            elif len(users) > 1:
                output[row][column] = 9
    return output
