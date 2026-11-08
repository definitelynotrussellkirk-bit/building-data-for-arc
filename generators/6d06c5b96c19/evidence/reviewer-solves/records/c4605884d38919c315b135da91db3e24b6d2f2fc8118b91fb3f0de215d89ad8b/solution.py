def solve(grid):
    """Remove the control column and rotate rows by the position of color 2."""
    marker_row = next(row for row, values in enumerate(grid) if values[0] == 2)
    body = [values[1:] for values in grid]
    if marker_row == 0:
        return body
    return body[-marker_row:] + body[:-marker_row]
