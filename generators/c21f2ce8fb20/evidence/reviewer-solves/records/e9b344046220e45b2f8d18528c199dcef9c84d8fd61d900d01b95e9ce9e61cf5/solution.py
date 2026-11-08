from collections import deque


def solve(grid):
    """Fill the compartment containing the most red (2) cells with azure (8)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    components = []

    for row in range(height):
        for col in range(width):
            if seen[row][col] or grid[row][col] == 5:
                continue

            queue = deque([(row, col)])
            seen[row][col] = True
            cells = []
            red_count = 0

            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                if grid[r][c] == 2:
                    red_count += 1

                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != 5
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            components.append((red_count, cells))

    result = [[0] * width for _ in range(height)]
    if not components:
        return result

    _, winning_cells = max(components, key=lambda item: item[0])
    for row, col in winning_cells:
        result[row][col] = 8
    return result
