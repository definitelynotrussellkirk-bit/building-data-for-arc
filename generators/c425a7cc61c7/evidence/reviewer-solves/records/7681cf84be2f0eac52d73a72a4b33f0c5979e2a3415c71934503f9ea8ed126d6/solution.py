from collections import deque


def solve(grid):
    """Extract the non-marker object in the top-left color and rotate it clockwise."""
    target = grid[0][0]
    height = len(grid)
    width = len(grid[0]) if height else 0

    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != target or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == target
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)

    candidates = [component for component in components if (0, 0) not in component]
    if not candidates:
        return [[target]]
    cells = max(candidates, key=len)

    min_row = min(r for r, _ in cells)
    max_row = max(r for r, _ in cells)
    min_col = min(c for _, c in cells)
    max_col = max(c for _, c in cells)
    cropped = [
        [target if (r, c) in set(cells) else 0 for c in range(min_col, max_col + 1)]
        for r in range(min_row, max_row + 1)
    ]

    return [list(row) for row in zip(*cropped[::-1])]
