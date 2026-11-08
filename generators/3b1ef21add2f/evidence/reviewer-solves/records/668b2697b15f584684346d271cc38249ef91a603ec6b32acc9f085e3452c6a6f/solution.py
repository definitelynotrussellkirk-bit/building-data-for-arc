def solve(grid):
    """Recolor color-2 cells that participate in a solid 2x2 color-2 block."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    marked = set()

    for row in range(height - 1):
        for col in range(width - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            if all(grid[r][c] == 2 for r, c in cells):
                marked.update(cells)

    for row, col in marked:
        out[row][col] = 3
    return out
