def solve(grid):
    """Collapse the two panels by aligned occupancy, preserving left overlaps."""
    height = len(grid)
    width = len(grid[0])
    separators = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError("expected one full-height gray separator")
    separator = separators[0]
    if separator * 2 + 1 != width:
        raise ValueError("separator must divide equal-width panels")

    output = []
    for row in grid:
        left = row[:separator]
        right = row[separator + 1 :]
        out_row = []
        for left_value, right_value in zip(left, right):
            if left_value != 0 and right_value == 0:
                out_row.append(2)
            elif left_value == 0 and right_value != 0:
                out_row.append(1)
            else:
                out_row.append(left_value)
        output.append(out_row)
    return output
