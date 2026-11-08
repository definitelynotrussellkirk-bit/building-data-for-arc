from collections import deque


def solve(grid):
    """Recolor each 4-connected body of 1s from the header above its left edge."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    seen = set()

    for row in range(1, height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            leftmost_col = col

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                leftmost_col = min(leftmost_col, c)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            color = grid[0][leftmost_col]
            for r, c in component:
                out[r][c] = color

    return out
