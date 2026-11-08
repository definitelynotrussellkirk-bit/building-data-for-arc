def solve(grid):
    """Replace each horizontal same-color run by its right-middle cell."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    for row_index, row in enumerate(grid):
        col = 0
        while col < width:
            color = row[col]
            if color == 0:
                col += 1
                continue

            start = col
            while col + 1 < width and row[col + 1] == color:
                col += 1
            end = col

            # Odd runs have one center.  For even runs, the examples choose
            # the cell just right of the geometric midpoint.
            middle = (start + end + 1) // 2
            out[row_index][middle] = color
            col += 1

    return out
