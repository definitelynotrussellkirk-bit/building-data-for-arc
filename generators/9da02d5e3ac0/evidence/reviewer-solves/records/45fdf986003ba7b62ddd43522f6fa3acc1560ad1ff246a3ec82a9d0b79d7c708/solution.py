def solve(grid):
    """Replace every 5 in a row with that row's first non-5 value."""
    output = []
    for row in grid:
        key = next((value for value in row if value != 5), None)
        if key is None:
            output.append(list(row))
        else:
            output.append([key if value == 5 else value for value in row])
    return output
