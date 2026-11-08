def solve(grid):
    """Select the indicated size-ranked component, crop it, and scale by two."""
    height, width = len(grid), len(grid[0])
    rank = grid[0][0]
    seen = {(0, 0)}
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            components.append(cells)
    components.sort(key=lambda cells: (len(cells), min(cells)))
    cells = components[rank - 1]
    top = min(r for r, c in cells)
    bottom = max(r for r, c in cells)
    left = min(c for r, c in cells)
    right = max(c for r, c in cells)
    selected = set(cells)
    output = []
    for r in range(top, bottom + 1):
        expanded = []
        for c in range(left, right + 1):
            expanded.extend([grid[r][c] if (r, c) in selected else 0] * 2)
        output.extend([expanded[:], expanded[:]])
    return output
