def solve(grid):
    """Recolor the earliest largest orthogonally connected orange component."""
    out = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    visited = set()
    best = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or (row, col) in visited:
                continue
            component = []
            pending = [(row, col)]
            visited.add((row, col))
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == 7 and (nr, nc) not in visited):
                        visited.add((nr, nc))
                        pending.append((nr, nc))
            if len(component) > len(best):
                best = component
    for row, col in best:
        out[row][col] = 8
    return out
