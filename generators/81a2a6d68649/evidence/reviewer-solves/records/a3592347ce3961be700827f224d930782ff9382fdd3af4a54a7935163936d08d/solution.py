from collections import deque


def solve(grid):
    """Recolor each 4-connected blue line by its orientation.

    Horizontal blue components become yellow (4); vertical blue components
    become orange (7). Other colors are preserved.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
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
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = {r for r, _ in component}
            cols = {c for _, c in component}
            if len(rows) == 1 and len(cols) > 1:
                replacement = 4
            elif len(cols) == 1 and len(rows) > 1:
                replacement = 7
            else:
                # The visible examples contain only straight lines. Preserve any
                # unsupported blue shape rather than guessing a destructive edit.
                replacement = 1

            for r, c in component:
                out[r][c] = replacement

    return out
