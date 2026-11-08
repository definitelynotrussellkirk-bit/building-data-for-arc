"""Visible-example solution for the prepared e1e7c467196f episode."""


def solve(grid):
    """Erase the two-row legend and apply its one-way color mapping to the body."""
    if len(grid) < 2:
        return [list(row) for row in grid]

    width = len(grid[0])
    mapping = {
        source: target
        for source, target in zip(grid[0], grid[1])
        if source != 0 and target != 0
    }

    output = []
    for row_index, row in enumerate(grid):
        if row_index < 2:
            output.append([0] * width)
        else:
            output.append([mapping.get(value, value) for value in row])
    return output
