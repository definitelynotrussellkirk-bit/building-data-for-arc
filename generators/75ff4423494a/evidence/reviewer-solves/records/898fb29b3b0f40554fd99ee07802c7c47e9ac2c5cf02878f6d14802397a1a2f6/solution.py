"""Visible-example solution for ARC task 75ff4423494a."""
from __future__ import annotations


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return orthogonally connected components of nonzero cells."""
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbour = (row + drow, col + dcol)
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    stack.append(neighbour)
        components.append(cells)
    return components


def solve(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    components = _components(grid)
    prototypes = [
        cells
        for cells in components
        if len(cells) > 1 and any(grid[row][col] == 8 for row, col in cells)
    ]
    prototype = min(
        prototypes,
        key=lambda cells: (
            -len(cells),
            min(row for row, _ in cells),
            min(col for _, col in cells),
        ),
    )
    prototype_set = set(prototype)

    top = min(row for row, _ in prototype)
    bottom = max(row for row, _ in prototype)
    left = min(col for _, col in prototype)
    right = max(col for _, col in prototype)
    template = [row[left : right + 1] for row in grid[top : bottom + 1]]

    origin_in_template = next(
        (row, col)
        for row, values in enumerate(template)
        for col, value in enumerate(values)
        if value == 8
    )
    original_origin = (top + origin_in_template[0], left + origin_in_template[1])
    destinations = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8 and (row, col) not in prototype_set
    ]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for anchor_row, anchor_col in [original_origin, *destinations]:
        shift_row = anchor_row - origin_in_template[0]
        shift_col = anchor_col - origin_in_template[1]
        for row, values in enumerate(template):
            for col, value in enumerate(values):
                if value == 0:
                    continue
                out_row, out_col = shift_row + row, shift_col + col
                if not (0 <= out_row < height and 0 <= out_col < width):
                    continue
                previous = output[out_row][out_col]
                if previous == 0:
                    output[out_row][out_col] = value
                elif previous != value:
                    output[out_row][out_col] = 9
    return output
