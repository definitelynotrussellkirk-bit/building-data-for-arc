from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Reverse the color sequence on the unique non-cyan 4-connected path."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    path_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 8
    }
    if not path_cells:
        return [row[:] for row in grid]

    def neighbors(cell: tuple[int, int]) -> list[tuple[int, int]]:
        row, col = cell
        return [
            other
            for other in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
            if other in path_cells
        ]

    if len(path_cells) == 1:
        ordered = [next(iter(path_cells))]
    else:
        endpoints = sorted(cell for cell in path_cells if len(neighbors(cell)) == 1)
        if len(endpoints) != 2:
            raise ValueError("non-background cells must form one simple path")

        ordered = []
        previous: tuple[int, int] | None = None
        current = endpoints[0]
        while True:
            ordered.append(current)
            choices = [cell for cell in neighbors(current) if cell != previous]
            if not choices:
                break
            if len(choices) != 1:
                raise ValueError("non-background cells must form one simple path")
            previous, current = current, choices[0]

        if len(ordered) != len(path_cells):
            raise ValueError("non-background cells must form one connected path")

    colors = [grid[row][col] for row, col in ordered]
    result = [row[:] for row in grid]
    for (row, col), color in zip(ordered, reversed(colors)):
        result[row][col] = color
    return result
