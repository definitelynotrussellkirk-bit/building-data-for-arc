def solve(grid):
    """Recolor every nonzero 4-connected singleton to maroon (9)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue

            has_same_color_neighbor = any(
                0 <= next_row < height
                and 0 <= next_col < width
                and grid[next_row][next_col] == color
                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                )
            )
            if not has_same_color_neighbor:
                output[row][col] = 9

    return output
