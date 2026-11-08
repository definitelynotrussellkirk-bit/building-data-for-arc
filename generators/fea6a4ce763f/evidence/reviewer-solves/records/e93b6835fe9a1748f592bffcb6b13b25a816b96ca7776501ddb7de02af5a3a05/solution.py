def solve(grid):
    """Crop the unique largest nonzero monochromatic 4-connected component."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue

            cells = set()
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)

    if not components:
        return [row[:] for row in grid]

    largest = max(components, key=len)
    top = min(r for r, _ in largest)
    bottom = max(r for r, _ in largest)
    left = min(c for _, c in largest)
    right = max(c for _, c in largest)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]
