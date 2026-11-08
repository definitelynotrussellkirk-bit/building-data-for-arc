def solve(grid):
    """Mark the interior cells of same-colour diagonal line segments."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    interior_cells = set()

    # A diagonal is scanned only from its maximal run's first cell.  Detect
    # against the untouched input, then recolour, so crossing runs do not alter
    # one another while they are being found.
    for dr, dc in ((1, 1), (1, -1)):
        for row in range(height):
            for col in range(width):
                color = grid[row][col]
                if color == 0:
                    continue

                previous_row = row - dr
                previous_col = col - dc
                if (
                    0 <= previous_row < height
                    and 0 <= previous_col < width
                    and grid[previous_row][previous_col] == color
                ):
                    continue

                run = []
                current_row, current_col = row, col
                while (
                    0 <= current_row < height
                    and 0 <= current_col < width
                    and grid[current_row][current_col] == color
                ):
                    run.append((current_row, current_col))
                    current_row += dr
                    current_col += dc

                if len(run) >= 3:
                    interior_cells.update(run[1:-1])

    for row, col in interior_cells:
        output[row][col] = 8

    return output
