from collections import deque


def solve(grid):
    """Fill each region bounded by color 5 using its extreme seed colors.

    A region with one nonzero seed color becomes solid.  A region with two or
    more seed colors becomes a checkerboard using the minimum and maximum seed
    colors, with the minimum color in the region's top-left parity class.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] == 5:
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
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
                        and grid[nr][nc] != 5
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            colors = sorted({grid[r][c] for r, c in cells if grid[r][c] != 0})
            if not colors:
                continue

            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            low, high = colors[0], colors[-1]

            if low == high:
                for r, c in cells:
                    out[r][c] = low
            else:
                for r, c in cells:
                    out[r][c] = low if (r - top + c - left) % 2 == 0 else high

    return out
