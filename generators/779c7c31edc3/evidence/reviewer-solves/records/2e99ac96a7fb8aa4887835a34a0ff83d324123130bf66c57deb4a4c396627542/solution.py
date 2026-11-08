from collections import deque


def solve(grid):
    """Hollow each solid monochrome rectangle, preserving its one-cell border."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
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

            # The examples contain filled axis-aligned rectangles. Restrict the
            # transformation to true rectangles so unrelated shapes are preserved.
            expected_area = (bottom - top + 1) * (right - left + 1)
            if len(component) != expected_area:
                continue

            for r, c in component:
                if top < r < bottom and left < c < right:
                    out[r][c] = 0

    return out
