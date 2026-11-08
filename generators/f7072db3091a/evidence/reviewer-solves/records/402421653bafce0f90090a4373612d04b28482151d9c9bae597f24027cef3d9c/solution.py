"""Visible-example solution for blind task f7072db3091a."""


def solve(grid):
    """Recolor both ends of every horizontal or vertical blue run orange."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    endpoints = set()

    # Maximal horizontal runs of blue cells.
    for row in range(height):
        col = 0
        while col < width:
            if grid[row][col] != 1:
                col += 1
                continue
            start = col
            while col + 1 < width and grid[row][col + 1] == 1:
                col += 1
            end = col
            if end > start:
                endpoints.add((row, start))
                endpoints.add((row, end))
            col += 1

    # Maximal vertical runs of blue cells.
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 1:
                row += 1
                continue
            start = row
            while row + 1 < height and grid[row + 1][col] == 1:
                row += 1
            end = row
            if end > start:
                endpoints.add((start, col))
                endpoints.add((end, col))
            row += 1

    for row, col in endpoints:
        out[row][col] = 7
    return out
