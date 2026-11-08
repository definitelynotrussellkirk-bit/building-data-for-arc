def solve(grid):
    """Remove the marker column and cyclically shift rows by the marker offset."""
    if not grid:
        return []
    marker_row = next(r for r, row in enumerate(grid) if row[0] == 2)
    body = [row[1:] for row in grid]
    if marker_row == 0:
        return body
    return body[-marker_row:] + body[:-marker_row]
