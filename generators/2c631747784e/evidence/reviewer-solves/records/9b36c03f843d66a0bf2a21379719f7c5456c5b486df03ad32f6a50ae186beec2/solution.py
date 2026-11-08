"""Visible-example-only solution for the blind ARC episode."""

from collections import Counter


def solve(grid):
    """Reverse the color sequence along the non-background 4-connected path."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    if len(cells) < 2:
        return [row[:] for row in grid]

    def neighbors(cell):
        row, col = cell
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            candidate = (row + drow, col + dcol)
            if candidate in cells:
                yield candidate

    adjacency = {cell: tuple(neighbors(cell)) for cell in cells}
    endpoints = [cell for cell, adjacent in adjacency.items() if len(adjacent) == 1]
    if len(endpoints) != 2 or any(len(adjacent) not in (1, 2) for adjacent in adjacency.values()):
        return [row[:] for row in grid]

    path = []
    previous = None
    current = min(endpoints)
    while current is not None:
        path.append(current)
        onward = [cell for cell in adjacency[current] if cell != previous]
        next_cell = onward[0] if onward else None
        previous, current = current, next_cell

    if len(path) != len(cells) or len(set(path)) != len(cells):
        return [row[:] for row in grid]

    values = [grid[row][col] for row, col in path]
    result = [row[:] for row in grid]
    for (row, col), value in zip(path, reversed(values)):
        result[row][col] = value
    return result
