"""Visible-example solution for blind task ad5998ad11d6."""

from collections import deque


def solve(grid):
    """Fill zero-valued regions enclosed by color 3 with color 4.

    Enclosure is defined by four-neighbor connectivity: zero cells reachable
    from the grid boundary remain background, while every other zero is a hole.
    The input grid is not mutated.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    exterior = set()
    queue = deque()

    def add_exterior(row, col):
        if grid[row][col] == 0 and (row, col) not in exterior:
            exterior.add((row, col))
            queue.append((row, col))

    for row in range(height):
        add_exterior(row, 0)
        if width > 1:
            add_exterior(row, width - 1)
    for col in range(width):
        add_exterior(0, col)
        if height > 1:
            add_exterior(height - 1, col)

    while queue:
        row, col = queue.popleft()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            next_row = row + drow
            next_col = col + dcol
            if (
                0 <= next_row < height
                and 0 <= next_col < width
                and grid[next_row][next_col] == 0
                and (next_row, next_col) not in exterior
            ):
                exterior.add((next_row, next_col))
                queue.append((next_row, next_col))

    return [
        [
            4 if value == 0 and (row, col) not in exterior else value
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]
