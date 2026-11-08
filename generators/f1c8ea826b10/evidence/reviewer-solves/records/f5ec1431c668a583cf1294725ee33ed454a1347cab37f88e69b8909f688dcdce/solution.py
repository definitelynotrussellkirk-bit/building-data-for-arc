from collections import deque


def solve(grid):
    """Complete each 5-bounded compartment with its min/max checkerboard."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 5 or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            cells = []
            colors = []

            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                if grid[r][c] not in (0, 5):
                    colors.append(grid[r][c])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            if not colors:
                continue

            low, high = min(colors), max(colors)
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            for r, c in cells:
                out[r][c] = low if (r - top + c - left) % 2 == 0 else high

    return out
