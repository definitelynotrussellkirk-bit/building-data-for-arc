def solve(grid):
    """Propagate the top row down-right while alternating colors 2 and 5."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]

    # Lower input rows are blank/background in the task. Rebuild them so cells
    # outside the narrowing wedge remain background even for a reused buffer.
    for row in range(1, height):
        output[row] = [7] * width
        for col in range(row, width - row):
            value = grid[0][col - row]
            if row % 2 == 1:
                if value == 2:
                    value = 5
                elif value == 5:
                    value = 2
            output[row][col] = value

    return output
