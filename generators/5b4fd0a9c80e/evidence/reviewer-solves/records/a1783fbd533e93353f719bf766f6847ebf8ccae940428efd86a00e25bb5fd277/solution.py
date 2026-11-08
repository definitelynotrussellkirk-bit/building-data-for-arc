from collections import deque


def solve(grid):
    """Extract non-background objects, sort by area, and stack them."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    objects = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            color = grid[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
            # The examples order by colored area; for equal areas, the
            # narrower/taller object comes first.
            objects.append((len(cells), c1 - c0 + 1, -(r1 - r0 + 1), crop))

    objects.sort(key=lambda item: item[:3])
    max_width = max(len(crop[0]) for *_, crop in objects)
    out = []
    for i, (*_, crop) in enumerate(objects):
        offset = (max_width - len(crop[0])) // 2
        for row in crop:
            out.append([0] * offset + row + [0] * (max_width - offset - len(row)))
        if i + 1 < len(objects):
            out.append([0] * max_width)
    return out
