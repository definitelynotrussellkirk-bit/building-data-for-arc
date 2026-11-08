def solve(grid):
    """Stack the row strips bracketed by the visible cyan block pairs."""
    result = []
    for row in grid:
        markers = [column for column, color in enumerate(row) if color == 8]
        if not markers:
            continue
        if len(markers) != 4 or markers[1] != markers[0] + 1 or markers[3] != markers[2] + 1:
            raise ValueError("Expected two two-cell cyan markers in each marked row")
        result.append(list(row[markers[1] + 1:markers[2]]))
    if not result or not result[0] or any(len(row) != len(result[0]) for row in result):
        raise ValueError("The marked strips must form a nonempty rectangular output")
    return result
