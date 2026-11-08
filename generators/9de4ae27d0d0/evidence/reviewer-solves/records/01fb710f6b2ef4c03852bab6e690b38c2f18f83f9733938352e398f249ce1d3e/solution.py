from collections import deque


def solve(grid):
    """Keep each 4-connected nonzero object iff it touches the grid border."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            touches_border = False

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                touches_border |= r in (0, height - 1) or c in (0, width - 1)

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

            if touches_border:
                for r, c in component:
                    out[r][c] = color

    return out
