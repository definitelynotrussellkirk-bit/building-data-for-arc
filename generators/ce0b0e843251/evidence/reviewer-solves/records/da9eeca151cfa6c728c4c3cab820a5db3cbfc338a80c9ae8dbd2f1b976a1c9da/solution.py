def solve(grid):
    """Fill each wall-bounded chamber with its marker, if it has one."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    walls = {5, 7}
    visited = set()
    for row in range(height):
        for col in range(width):
            if (row, col) in visited or grid[row][col] in walls:
                continue
            stack = [(row, col)]
            visited.add((row, col))
            cells = []
            markers = set()
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                if grid[r][c] != 0:
                    markers.add(grid[r][c])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited
                            and grid[nr][nc] not in walls):
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            if len(markers) > 1:
                raise ValueError("The visible examples do not define mixed-marker chambers")
            if markers:
                color = next(iter(markers))
                for r, c in cells:
                    result[r][c] = color
    return result
