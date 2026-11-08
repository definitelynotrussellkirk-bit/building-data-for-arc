from collections import deque


def solve(grid):
    """Recolor each nonzero 4-connected object that touches exactly one border."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []

            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            touched = {
                side
                for r, c in cells
                for side, condition in (
                    ("top", r == 0),
                    ("bottom", r == height - 1),
                    ("left", c == 0),
                    ("right", c == width - 1),
                )
                if condition
            }
            if color == 7 and len(touched) == 1:
                for r, c in cells:
                    out[r][c] = 3

    return out
