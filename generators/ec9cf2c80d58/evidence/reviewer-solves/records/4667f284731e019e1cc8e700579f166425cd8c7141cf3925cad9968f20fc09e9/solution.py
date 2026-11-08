"""Visible-example solution for the colored-band extent task."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]

    holes = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] == 0
    ]

    for row, col in holes:
        color = None
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width and original[nr][nc] != 0:
                color = original[nr][nc]
                break
        if color is None:
            continue

        row_extent = sum(original[row][c] in (0, color) for c in range(width))
        col_extent = sum(original[r][col] in (0, color) for r in range(height))
        if row_extent >= col_extent:
            cells = ((r, col) for r in range(height))
        else:
            cells = ((row, c) for c in range(width))

        for r, c in cells:
            if original[r][c] in (0, color):
                output[r][c] = 0

    return output
