def solve(grid):
    """Recolor the horizontally middle nonblack object to azure (8)."""
    result = [list(row) for row in grid]
    if not result or not result[0]:
        return result

    height, width = len(result), len(result[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            cells = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append(cells)

    if not objects:
        return result
    objects.sort(key=lambda cells: (
        sum(c for r, c in cells) / len(cells),
        sum(r for r, c in cells) / len(cells),
    ))
    for row, col in objects[len(objects) // 2]:
        result[row][col] = 8
    return result
