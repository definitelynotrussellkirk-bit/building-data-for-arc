def solve(grid):
    """Append color 8 to each unblocked horizontal 2,3 marker."""
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c in range(len(row) - 2):
            if row[c : c + 3] == [2, 3, 0]:
                result[r][c + 2] = 8
    return result
