def solve(grid):
    """Replace every nonzero cell by a clipped four-neighbour cross in color 8."""
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value == 0:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr = row_index + dr
                cc = col_index + dc
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[rr]):
                    output[rr][cc] = 8
    return output
