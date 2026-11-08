def solve(grid):
    """Project left-edge row markers and top-edge column markers to intersections."""
    rows = [r for r in range(1, len(grid)) if grid[r][0] == 2]
    cols = [c for c in range(1, len(grid[0])) if grid[0][c] == 1]

    output = [[0 for _ in row] for row in grid]
    for r in rows:
        for c in cols:
            output[r][c] = 3
    return output
