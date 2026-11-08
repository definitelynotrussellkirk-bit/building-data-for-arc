def solve(grid):
    """Fill the gap in rows containing exactly two equal non-background cells."""
    result = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        occupied = [column for column, color in enumerate(row) if color != 0]
        if len(occupied) != 2:
            continue
        left, right = occupied
        color = row[left]
        if row[right] != color:
            continue
        result[row_index][left : right + 1] = [color] * (right - left + 1)
    return result
