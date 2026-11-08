"""Visible-only hypothesis: crop the largest monochromatic component."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    largest = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            component = []
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            # Strict comparison retains the first component in row-major order
            # when cell counts are tied, as in visible training example 0.
            if len(component) > len(largest):
                largest = component
    if not largest:
        return [[0]]
    r0 = min(r for r, c in largest)
    r1 = max(r for r, c in largest)
    c0 = min(c for r, c in largest)
    c1 = max(c for r, c in largest)
    result = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in largest:
        result[r - r0][c - c0] = grid[r][c]
    return result
