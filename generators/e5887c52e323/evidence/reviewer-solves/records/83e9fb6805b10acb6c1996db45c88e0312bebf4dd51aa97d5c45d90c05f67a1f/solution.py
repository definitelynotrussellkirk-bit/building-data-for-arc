def solve(grid):
    """Mark the elbow of every isolated red L-triomino yellow."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if len(component) != 3:
                continue
            rows = {r for r, _ in component}
            cols = {c for _, c in component}
            if len(rows) != 2 or len(cols) != 2:
                continue

            cells = set(component)
            for r, c in component:
                neighbors = sum(
                    (r + dr, c + dc) in cells
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                )
                if neighbors == 2:
                    out[r][c] = 4
                    break

    return out
