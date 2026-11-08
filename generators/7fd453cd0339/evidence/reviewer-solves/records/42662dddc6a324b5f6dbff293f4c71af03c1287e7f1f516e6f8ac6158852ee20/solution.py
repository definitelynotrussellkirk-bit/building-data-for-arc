def solve(grid):
    """Keep the corners of each separate monochrome foreground rectangle."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0] * width for _ in range(height)]
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            component = {(row, col)}
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                rr, cc = pending.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc),
                               (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        component.add((nr, nc))
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            top = min(rr for rr, _ in component)
            bottom = max(rr for rr, _ in component)
            left = min(cc for _, cc in component)
            right = max(cc for _, cc in component)
            for rr in {top, bottom}:
                for cc in {left, right}:
                    if (rr, cc) in component:
                        result[rr][cc] = color
    return result
