from collections import deque


def solve(grid):
    """Fill the interior of every blue rectangular frame containing red.

    Blue (1) frames stay unchanged.  A frame whose interior contains at least
    one red (2) cell has each remaining black (0) interior cell recolored green
    (3); red marker cells are preserved.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != 1 or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
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

            top = min(r for r, _ in component)
            bottom = max(r for r, _ in component)
            left = min(c for _, c in component)
            right = max(c for _, c in component)
            if bottom - top < 2 or right - left < 2:
                continue

            perimeter = {
                (r, c)
                for r in range(top, bottom + 1)
                for c in range(left, right + 1)
                if r in (top, bottom) or c in (left, right)
            }
            if set(component) != perimeter:
                continue

            has_marker = any(
                grid[r][c] == 2
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
            )
            if not has_marker:
                continue

            for r in range(top + 1, bottom):
                for c in range(left + 1, right):
                    if grid[r][c] == 0:
                        out[r][c] = 3

    return out
