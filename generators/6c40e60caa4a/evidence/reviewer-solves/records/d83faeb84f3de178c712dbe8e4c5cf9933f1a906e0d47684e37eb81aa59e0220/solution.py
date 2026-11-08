from collections import deque


def solve(grid):
    """Fill every 1-bounded non-1 region containing a red (2) seed with green (3)."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 1 or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            component = []
            touches_border = False
            has_seed = False

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                touches_border |= r in (0, height - 1) or c in (0, width - 1)
                has_seed |= grid[r][c] == 2

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if grid[nr][nc] == 1 or (nr, nc) in seen:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))

            if has_seed and not touches_border:
                for r, c in component:
                    out[r][c] = 3

    return out
