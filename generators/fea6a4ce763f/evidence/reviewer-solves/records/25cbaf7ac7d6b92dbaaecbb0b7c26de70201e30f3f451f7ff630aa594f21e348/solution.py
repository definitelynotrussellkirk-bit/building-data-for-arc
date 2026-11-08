from collections import deque


def solve(grid):
    """Return the tight crop of the largest non-background 4-connected component."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    best = None

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or seen[row][col]:
                continue

            queue = deque([(row, col)])
            seen[row][col] = True
            cells = []

            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            candidate = (len(cells), color, cells)
            if best is None or candidate[0] > best[0]:
                best = candidate

    if best is None:
        return []

    _, color, cells = best
    min_row = min(r for r, _ in cells)
    max_row = max(r for r, _ in cells)
    min_col = min(c for _, c in cells)
    max_col = max(c for _, c in cells)
    cell_set = set(cells)

    return [
        [color if (r, c) in cell_set else 0 for c in range(min_col, max_col + 1)]
        for r in range(min_row, max_row + 1)
    ]
