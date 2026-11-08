from __future__ import annotations

from collections import deque


def solve(grid):
    """Crop each nonzero object and stack crops by occupied area, largest first."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [list(source[left : right + 1]) for source in grid[top : bottom + 1]]
            objects.append((len(cells), crop))

    objects.sort(key=lambda item: item[0], reverse=True)
    output_width = max(len(crop[0]) for _, crop in objects)
    output = []
    for index, (_, crop) in enumerate(objects):
        if index:
            output.append([0] * output_width)
        for row in crop:
            output.append(row + [0] * (output_width - len(row)))
    return output
