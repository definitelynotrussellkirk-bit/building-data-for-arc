from copy import deepcopy


def solve(grid):
    """Preserve the two header rows and paint the body from row-0's cycle."""
    if not isinstance(grid, list) or len(grid) < 2:
        raise ValueError("expected at least two rows")
    if not grid[0] or any(not isinstance(row, list) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    output = deepcopy(grid)
    cycle = grid[0]
    for row_index in range(2, len(output)):
        color = cycle[(row_index - 2) % width]
        output[row_index] = [color] * width
    return output
