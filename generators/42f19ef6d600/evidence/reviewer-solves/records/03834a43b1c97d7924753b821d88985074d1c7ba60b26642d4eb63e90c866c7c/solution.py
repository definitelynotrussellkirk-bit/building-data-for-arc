from collections import Counter


def solve(grid):
    """Extend the exposed edges of two-dimensional colored shapes with blue (2)."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    result = [row[:] for row in grid]

    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background:
                continue

            for dr, dc in directions:
                out_row, out_col = row + dr, col + dc
                in_row, in_col = row - dr, col - dc
                if not (0 <= out_row < height and 0 <= out_col < width):
                    continue
                if not (0 <= in_row < height and 0 <= in_col < width):
                    continue
                if grid[out_row][out_col] != background:
                    continue
                if grid[in_row][in_col] != color:
                    continue

                # A perpendicular same-color neighbor distinguishes a 2-D body
                # from a one-cell-wide horizontal or vertical line.
                if dr:
                    has_side_support = (
                        (col > 0 and grid[row][col - 1] == color)
                        or (col + 1 < width and grid[row][col + 1] == color)
                    )
                else:
                    has_side_support = (
                        (row > 0 and grid[row - 1][col] == color)
                        or (row + 1 < height and grid[row + 1][col] == color)
                    )

                if has_side_support:
                    result[out_row][out_col] = 2

    return result
