from collections import deque


def solve(grid):
    """Replace each 4-connected colored object by its bounding-box perimeter."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in component)
            bottom = max(r for r, _ in component)
            left = min(c for _, c in component)
            right = max(c for _, c in component)

            for r, c in component:
                out[r][c] = 0

            for c in range(left, right + 1):
                out[top][c] = color
                out[bottom][c] = color
            for r in range(top, bottom + 1):
                out[r][left] = color
                out[r][right] = color

    return out
