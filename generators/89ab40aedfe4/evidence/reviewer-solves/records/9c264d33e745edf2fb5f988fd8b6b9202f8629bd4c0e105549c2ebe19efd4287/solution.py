"""Stable population sorting of the bit columns next to full-height carriers."""


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a rectangular nonempty grid")
    height, width = len(grid), len(grid[0])
    foreground = grid[0][0]
    bit_columns = []
    for column in range(width - 1):
        if (all(grid[row][column] == foreground for row in range(height))
                and grid[0][column + 1] == foreground
                and (column == 0 or grid[0][column - 1] == 0)):
            bit_columns.append(column + 1)
    patterns = [[grid[row][column] for row in range(height)] for column in bit_columns]
    # Python's stable sort keeps equal populations in their source order.
    ordered = sorted(patterns, key=lambda cells: sum(c == foreground for c in cells))
    output = [list(row) for row in grid]
    for column, cells in zip(bit_columns, ordered):
        for row, color in enumerate(cells):
            output[row][column] = color
    return output
