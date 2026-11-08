def solve(grid):
    """Use the first nonzero top-row value to recolor body cells equal to 1."""
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    try:
        target = next(value for value in grid[0] if value != 0)
    except StopIteration as exc:
        raise ValueError("top row must contain a nonzero legend color") from exc

    output = [[0 for _ in row] for row in grid]
    for row in range(1, len(grid)):
        for column, value in enumerate(grid[row]):
            if value == 1:
                output[row][column] = target
    return output
