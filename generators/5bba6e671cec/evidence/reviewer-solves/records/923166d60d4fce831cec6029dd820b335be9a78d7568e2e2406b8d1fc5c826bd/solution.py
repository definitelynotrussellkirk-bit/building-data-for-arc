def solve(grid):
    """Cycle every non-structural color to the next larger present color.

    Colors 4 and 7 form the unchanged structure.  The remaining distinct
    colors are ordered numerically; each is replaced by its successor, with
    the largest wrapping to the smallest.
    """
    movable = sorted({value for row in grid for value in row if value not in {4, 7}})
    if len(movable) < 2:
        return [row[:] for row in grid]

    replacement = {
        value: movable[(index + 1) % len(movable)]
        for index, value in enumerate(movable)
    }
    return [
        [replacement.get(value, value) for value in row]
        for row in grid
    ]
