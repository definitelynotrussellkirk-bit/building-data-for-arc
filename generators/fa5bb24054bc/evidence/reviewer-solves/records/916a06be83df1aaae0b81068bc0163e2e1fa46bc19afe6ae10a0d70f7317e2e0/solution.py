"""Visible-example solution for task fa5bb24054bc."""

from collections import deque


def _split_panels(grid):
    """Return maximal nonblank column runs, with each run tightly cropped."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    nonblank = [any(grid[r][c] != 0 for r in range(height)) for c in range(width)]

    panels = []
    c = 0
    while c < width:
        while c < width and not nonblank[c]:
            c += 1
        if c == width:
            break
        start = c
        while c < width and nonblank[c]:
            c += 1
        stop = c

        occupied_rows = [
            r for r in range(height)
            if any(grid[r][x] != 0 for x in range(start, stop))
        ]
        top, bottom = min(occupied_rows), max(occupied_rows) + 1
        panels.append([row[start:stop] for row in grid[top:bottom]])

    return panels


def _features(panel):
    """Compute filled-cell area and number of enclosed 4-connected holes."""
    height = len(panel)
    width = len(panel[0]) if height else 0
    area = sum(cell != 0 for row in panel for cell in row)

    # A one-cell zero frame makes every exterior zero reachable from (0, 0).
    padded = [[0] * (width + 2)]
    padded.extend([[0] + [int(cell != 0) for cell in row] + [0] for row in panel])
    padded.append([0] * (width + 2))

    ph, pw = height + 2, width + 2
    seen = [[False] * pw for _ in range(ph)]

    def flood(sr, sc):
        queue = deque([(sr, sc)])
        seen[sr][sc] = True
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < ph
                    and 0 <= nc < pw
                    and not seen[nr][nc]
                    and padded[nr][nc] == 0
                ):
                    seen[nr][nc] = True
                    queue.append((nr, nc))

    flood(0, 0)
    holes = 0
    for r in range(1, ph - 1):
        for c in range(1, pw - 1):
            if padded[r][c] == 0 and not seen[r][c]:
                holes += 1
                flood(r, c)

    return area, holes


def solve(grid):
    panels = _split_panels(grid)
    features = [_features(panel) for panel in panels]
    n = len(features)
    output = [[0] * n for _ in range(n)]

    for i, (area_i, holes_i) in enumerate(features):
        for j, (area_j, holes_j) in enumerate(features):
            if i == j:
                value = 5
            else:
                same_area = area_i == area_j
                same_holes = holes_i == holes_j
                if same_area and same_holes:
                    value = 6
                elif same_area:
                    value = 2
                elif same_holes:
                    value = 3
                else:
                    value = 0
            output[i][j] = value

    return output
