def solve(grid):
    """Select a colored component by the guide rectangle and preserve its crop."""
    height, width = len(grid), len(grid[0])
    guide = [(r, c) for r, row in enumerate(grid)
             for c, color in enumerate(row) if color == 7]
    if not guide:
        raise ValueError("Expected guide marks")
    top, bottom = min(r for r, _ in guide), max(r for r, _ in guide)
    left, right = min(c for _, c in guide), max(c for _, c in guide)
    visited = set()
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color in (5, 7) or (row, column) in visited:
                continue
            stack = [(row, column)]
            visited.add((row, column))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            if top <= (r0 + r1) // 2 <= bottom and left <= (c0 + c1) // 2 <= right:
                return [list(values[c0:c1 + 1]) for values in grid[r0:r1 + 1]]
    raise ValueError("No eligible component")
