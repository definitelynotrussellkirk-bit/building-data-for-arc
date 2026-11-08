from collections import deque


def solve(grid):
    """Fill each zero-valued hole: gray for one cell, orange otherwise."""
    out = [row[:] for row in grid]
    height = len(out)
    if height == 0:
        return out
    width = len(out[0])
    if width == 0:
        return out

    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if out[start_r][start_c] != 0 or seen[start_r][start_c]:
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
            component = []
            touches_border = False

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                if r in (0, height - 1) or c in (0, width - 1):
                    touches_border = True

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and out[nr][nc] == 0
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if not touches_border:
                fill = 5 if len(component) == 1 else 7
                for r, c in component:
                    out[r][c] = fill

    return out
