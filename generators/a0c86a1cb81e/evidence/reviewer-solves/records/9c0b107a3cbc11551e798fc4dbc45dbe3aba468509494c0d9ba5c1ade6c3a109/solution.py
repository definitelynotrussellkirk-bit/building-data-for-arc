def solve(grid):
    """Recolor each orthogonal bend in the 3-colored paths from 3 to 6."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3:
                continue

            horizontal_neighbors = sum(
                0 <= next_col < width and grid[row][next_col] == 3
                for next_col in (col - 1, col + 1)
            )
            vertical_neighbors = sum(
                0 <= next_row < height and grid[next_row][col] == 3
                for next_row in (row - 1, row + 1)
            )

            # A path bend has exactly two orthogonal neighbors: one horizontal
            # and one vertical. Straight segments and endpoints stay color 3.
            if horizontal_neighbors == 1 and vertical_neighbors == 1:
                result[row][col] = 6

    return result
