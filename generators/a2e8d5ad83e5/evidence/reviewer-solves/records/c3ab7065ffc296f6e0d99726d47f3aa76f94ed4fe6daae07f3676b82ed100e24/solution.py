def solve(grid):
    """Extend each solid square's center axes; unlike rays cancel to black."""
    height, width = len(grid), len(grid[0])
    seen = set()
    squares = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            component = {(row, col)}
            seen.add((row, col))
            pending = [(row, col)]
            while pending:
                r, c = pending.pop()
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        component.add((nr, nc))
                        pending.append((nr, nc))
            r0 = min(r for r, _ in component)
            r1 = max(r for r, _ in component)
            c0 = min(c for _, c in component)
            c1 = max(c for _, c in component)
            side = r1 - r0 + 1
            if side >= 2 and side == c1 - c0 + 1 and len(component) == side * side:
                squares.append(((r0 + r1) // 2, (c0 + c1) // 2, color))
    output = [list(row) for row in grid]
    for r in range(height):
        for c in range(width):
            colors = {color for sr, sc, color in squares if r == sr or c == sc}
            if colors:
                output[r][c] = next(iter(colors)) if len(colors) == 1 else 0
    return output
