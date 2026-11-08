"""Visible-example solution for task 8f6a6ec3ae21."""


def solve(grid):
    h = len(grid)
    w = len(grid[0])
    selected_rows = [r for r in range(h) if grid[r][0] == 1]
    selected_cols = [c for c in range(w) if grid[0][c] == 2]
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r in selected_rows:
        for c in selected_cols:
            output[r][c] = 8
    return output
