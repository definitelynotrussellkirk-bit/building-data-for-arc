"""Solution inferred from this episode's visible examples; earlier exposure disclosed."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 4}
    while remaining:
        point = min(remaining)
        remaining.remove(point)
        stack = [point]
        cells = [point]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.append(neighbor)
                    stack.append(neighbor)
        top = min(r for r, c in cells)
        bottom = max(r for r, c in cells)
        left = min(c for r, c in cells)
        right = max(c for r, c in cells)
        colors = {grid[r][c] for r in range(top+1, bottom)
                  for c in range(left+1, right) if grid[r][c] not in (0, 4)}
        if len(colors) != 1:
            raise ValueError('Expected one interior marker color per yellow rectangle')
        color = next(iter(colors))
        for r in range(top+1, bottom):
            for c in range(left+1, right):
                if result[r][c] == 0:
                    result[r][c] = color
    return result
