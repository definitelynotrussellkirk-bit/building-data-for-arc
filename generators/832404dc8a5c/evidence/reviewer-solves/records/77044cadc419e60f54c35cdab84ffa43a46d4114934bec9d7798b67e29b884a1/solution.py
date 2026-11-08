"""Exposed post-repair solve, implemented from the visible challenge."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    selected_rows = {r for r in range(h) if grid[r][0] == grid[r][-1] == 4}
    selected_columns = {c for c in range(w) if grid[0][c] == grid[-1][c] == 4}
    substitution = {0: 8, 8: 0, 6: 7, 7: 6}
    return [[substitution.get(value, value)
             if r in selected_rows or c in selected_columns else value
             for c, value in enumerate(row)]
            for r, row in enumerate(grid)]
