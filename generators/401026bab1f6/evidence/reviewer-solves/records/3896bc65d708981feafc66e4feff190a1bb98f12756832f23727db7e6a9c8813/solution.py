"""Inferred only from the four visible demonstration pairs."""


def solve(grid):
    result = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width)
                 if grid[r][c] == 1}
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        top = min(r for r, _ in component)
        bottom = max(r for r, _ in component)
        left = min(c for _, c in component)
        right = max(c for _, c in component)
        for r in range(top + 1, bottom):
            for c in range(left + 1, right):
                reflected_row = top + bottom - r
                if grid[r][c] == 4 and grid[reflected_row][c] == 0:
                    result[reflected_row][c] = 7
    return result
