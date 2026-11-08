def solve(grid):
    """Shift each object's non-bottom/non-right-edge cells one step right."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = set()
    stay = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = set()
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                component.add((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))

            bottom = max(r for r, _ in component)
            right = max(c for _, c in component)
            stay.update((r, c) for r, c in component if r == bottom or c == right)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        for c in range(width):
            if (r, c) in stay:
                output[r][c] = grid[r][c]
            elif c > 0 and grid[r][c - 1] != 0 and (r, c - 1) not in stay:
                output[r][c] = grid[r][c - 1]
    return output
