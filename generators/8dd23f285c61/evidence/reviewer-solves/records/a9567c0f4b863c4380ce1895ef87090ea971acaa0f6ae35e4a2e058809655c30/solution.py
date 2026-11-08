def solve(grid):
    """Emit color-8 rays from every color-2 cell until color-5 barriers."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    emitters = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    for row, col in emitters:
        out[row][col] = 8
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ray_row = row + delta_row
            ray_col = col + delta_col
            while 0 <= ray_row < height and 0 <= ray_col < width:
                if grid[ray_row][ray_col] == 5:
                    break
                out[ray_row][ray_col] = 8
                ray_row += delta_row
                ray_col += delta_col

    return out
