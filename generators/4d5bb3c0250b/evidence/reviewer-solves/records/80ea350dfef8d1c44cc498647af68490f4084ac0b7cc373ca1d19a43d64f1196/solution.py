"""Extract the unique chamber containing just one nonzero color."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    row_lines = [
        r for r, row in enumerate(grid)
        if row[0] != 0 and all(value == row[0] for value in row)
    ]
    column_lines = [
        c for c in range(width)
        if grid[0][c] != 0
        and all(grid[r][c] == grid[0][c] for r in range(height))
    ]
    row_bounds = [-1] + row_lines + [height]
    column_bounds = [-1] + column_lines + [width]
    candidates = []
    for top, bottom in zip(row_bounds, row_bounds[1:]):
        for left, right in zip(column_bounds, column_bounds[1:]):
            chamber = [row[left + 1:right] for row in grid[top + 1:bottom]]
            if not chamber or not chamber[0]:
                continue
            colors = {value for row in chamber for value in row if value != 0}
            if len(colors) == 1:
                candidates.append(chamber)
    if len(candidates) != 1:
        raise ValueError("Expected one chamber with a single nonzero color")
    return candidates[0]
