"""Visible-example solver for the exposed post-repair solve episode."""


def solve(grid):
    result = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    visited = set()
    pattern = {(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)}
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3 or (row, col) in visited:
                continue
            pending = [(row, col)]
            visited.add((row, col))
            component = []
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < height and 0 <= nc < width
                                and grid[nr][nc] == 3 and (nr, nc) not in visited):
                            visited.add((nr, nc))
                            pending.append((nr, nc))
            if len(component) != 5:
                continue
            top = min(r for r, c in component)
            left = min(c for r, c in component)
            if {(r - top, c - left) for r, c in component} == pattern:
                for r, c in component:
                    result[r][c] = 2
    return result
