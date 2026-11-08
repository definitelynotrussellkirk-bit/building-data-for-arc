def solve(grid):
    """Merge complementary panels; preserve the left panel if they clash or gap."""
    middle = len(grid[0]) // 2
    left = [list(row[:middle]) for row in grid]
    right = [list(row[middle + 1:]) for row in grid]
    complementary = all(
        (a != 0) != (b != 0)
        for left_row, right_row in zip(left, right)
        for a, b in zip(left_row, right_row)
    )
    if not complementary:
        return left
    return [[a or b for a, b in zip(lrow, rrow)] for lrow, rrow in zip(left, right)]
