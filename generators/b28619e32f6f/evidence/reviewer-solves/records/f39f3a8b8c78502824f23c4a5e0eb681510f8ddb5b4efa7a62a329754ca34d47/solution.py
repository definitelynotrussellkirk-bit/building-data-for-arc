from collections import deque


def solve(grid):
    """Color every zero-valued chamber enclosed by 2-valued walls.

    The examples use three chamber-width bands.  A chamber whose shorter
    bounding-box span is 1--2 cells becomes 8, 3--4 becomes 4, and 5+ becomes
    3.  Existing wall/marker cells are preserved.
    """
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]

    for r0 in range(h):
        for c0 in range(w):
            if seen[r0][c0] or grid[r0][c0] != 0:
                continue

            q = deque([(r0, c0)])
            seen[r0][c0] = True
            cells = []
            touches_edge = False
            min_r = max_r = r0
            min_c = max_c = c0

            while q:
                r, c = q.popleft()
                cells.append((r, c))
                min_r = min(min_r, r)
                max_r = max(max_r, r)
                min_c = min(min_c, c)
                max_c = max(max_c, c)
                if r in (0, h - 1) or c in (0, w - 1):
                    touches_edge = True

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == 0
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            if touches_edge:
                continue

            short_span = min(max_r - min_r + 1, max_c - min_c + 1)
            color = 8 if short_span <= 2 else 4 if short_span <= 4 else 3
            for r, c in cells:
                out[r][c] = color

    return out
