def solve(grid):
    """Overlay the two panels around the solid separator row.

    A cell is colored 3 when either panel has a nonzero cell there;
    otherwise it remains 0.
    """
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")

    separators = [
        index
        for index, row in enumerate(grid)
        if row[0] != 0 and all(value == row[0] for value in row)
        and index == len(grid) - index - 1
    ]
    if len(separators) != 1:
        raise ValueError("expected one centered solid nonzero separator row")

    separator = separators[0]
    top = grid[:separator]
    bottom = grid[separator + 1 :]
    if len(top) != len(bottom):
        raise ValueError("panels must have equal heights")

    return [
        [3 if top[r][c] != 0 or bottom[r][c] != 0 else 0 for c in range(width)]
        for r in range(len(top))
    ]
