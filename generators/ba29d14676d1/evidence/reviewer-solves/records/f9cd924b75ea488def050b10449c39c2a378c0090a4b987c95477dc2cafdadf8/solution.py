"""Visible-example solution: reflect each tile in place across its vertical axis."""


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    separators = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    boundaries = [-1] + separators + [width]
    result = [list(row) for row in grid]
    for left, right in zip(boundaries, boundaries[1:]):
        for r in range(height):
            result[r][left+1:right] = grid[r][left+1:right][::-1]
    return result
