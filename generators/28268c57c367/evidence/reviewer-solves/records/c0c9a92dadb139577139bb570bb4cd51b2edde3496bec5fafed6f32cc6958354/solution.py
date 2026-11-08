"""Visible-example solution; does not import the generator or reference."""
def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    walls = [c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid)]
    if len(walls) != 1:
        raise ValueError('Expected exactly one full-height gray wall')
    wall = walls[0]
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        color = None
        for c in range(wall):
            value = row[c]
            if color is None and value not in (0, 5):
                color = value
            elif value == 0 and color is not None:
                result[r][c] = color
    return result
