"""Visible-example solution for d3c9fc4479d8."""


def solve(grid):
    """Read adjacent nonzero color pairs from row 0, then recolor the body once."""
    if not grid:
        return []

    legend = grid[0]
    mapping = {}
    col = 0
    while col + 1 < len(legend):
        source, target = legend[col], legend[col + 1]
        if source != 0 and target != 0:
            mapping[source] = target
            col += 2
        else:
            col += 1

    return [[mapping.get(value, value) for value in row] for row in grid[1:]]
