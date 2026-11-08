from collections import deque


def solve(grid):
    """Recolor each orange (7) component touching the outer border green (3)."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or (row, col) in seen:
                continue

            component = []
            touches_border = False
            queue = deque([(row, col)])
            seen.add((row, col))

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                if r in (0, height - 1) or c in (0, width - 1):
                    touches_border = True

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 7
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            if touches_border:
                for r, c in component:
                    out[r][c] = 3

    return out
