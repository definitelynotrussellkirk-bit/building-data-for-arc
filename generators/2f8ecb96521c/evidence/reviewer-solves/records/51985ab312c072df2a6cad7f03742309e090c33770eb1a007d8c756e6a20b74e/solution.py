def solve(grid):
    """Recolor rectangle interiors by increasing component size."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 4 or (row, col) in seen:
                continue
            seen.add((row, col))
            cells = [(row, col)]
            pending = [(row, col)]
            while pending:
                r, c = pending.pop()
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == 4 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
                        pending.append((nr, nc))
            components.append(cells)

    for rank, cells in enumerate(sorted(components, key=len), start=1):
        top = min(r for r, c in cells)
        bottom = max(r for r, c in cells)
        left = min(c for r, c in cells)
        right = max(c for r, c in cells)
        for r, c in cells:
            if top < r < bottom and left < c < right:
                result[r][c] = rank
    return result
