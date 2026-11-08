def solve(grid):
    """Change the zero in every horizontal 7-0-7 triplet to 3."""
    output = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        for col in range(1, len(row) - 1):
            if row[col - 1 : col + 2] == [7, 0, 7]:
                output[row_index][col] = 3
    return output
