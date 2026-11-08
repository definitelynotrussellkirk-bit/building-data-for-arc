"""Blind solution for the visible ARC examples."""
from collections import deque


def solve(grid):
    if not grid or not grid[0]:
        return []

    height, width = len(grid), len(grid[0])
    colors = [value for value in grid[0] if value not in (0, 8)]

    seen = set()
    components = []
    for r in range(1, height):
        for c in range(width):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)

    # The visible examples pair left-to-right header colors with gray objects
    # in descending order of area, then pack recolored objects with one blank
    # column between them while bottom-aligning their original orientations.
    components.sort(key=len, reverse=True)
    objects = []
    for color, cells in zip(colors, components):
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        obj = [[0] * (max_c - min_c + 1) for _ in range(max_r - min_r + 1)]
        for r, c in cells:
            obj[r - min_r][c - min_c] = color
        objects.append(obj)

    if not objects:
        return []

    out_h = max(len(obj) for obj in objects)
    out_w = sum(len(obj[0]) for obj in objects) + len(objects) - 1
    output = [[0] * out_w for _ in range(out_h)]

    left = 0
    for obj in objects:
        top = out_h - len(obj)
        for r, row in enumerate(obj):
            for c, value in enumerate(row):
                if value:
                    output[top + r][left + c] = value
        left += len(obj[0]) + 1

    return output
