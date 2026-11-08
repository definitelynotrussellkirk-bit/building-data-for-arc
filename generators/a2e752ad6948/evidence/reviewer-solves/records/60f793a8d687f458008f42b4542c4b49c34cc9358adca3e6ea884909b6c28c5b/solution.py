from collections import deque


def solve(grid):
    """Fill each colored rectangular frame with a two-color checkerboard.

    The frame color supplies one checkerboard color.  The sole non-background,
    non-frame cell inside the rectangle supplies the other color.  The interior
    checkerboard always starts with the marker color at its top-left cell.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]

    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or seen[r0][c0]:
                continue

            # Isolate a 4-connected monochrome component.  Rectangular frames
            # are connected, while their interior marker is a separate component.
            q = deque([(r0, c0)])
            seen[r0][c0] = True
            cells = []
            while q:
                r, c = q.popleft()
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
                        q.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            if bottom - top < 2 or right - left < 2:
                continue

            perimeter = {
                (r, c)
                for r in range(top, bottom + 1)
                for c in range(left, right + 1)
                if r in (top, bottom) or c in (left, right)
            }
            if set(cells) != perimeter:
                continue

            marker_colors = {
                grid[r][c]
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
                if grid[r][c] not in (0, color)
            }
            if len(marker_colors) != 1:
                continue
            marker = next(iter(marker_colors))

            for r in range(top + 1, bottom):
                for c in range(left + 1, right):
                    out[r][c] = marker if (r - top - 1 + c - left - 1) % 2 == 0 else color

    return out
