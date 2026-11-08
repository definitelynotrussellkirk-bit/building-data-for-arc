from __future__ import annotations

from collections import deque


def _largest_same_color_component(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    best = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
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
            if len(component) > len(best):
                best = component
    return best


def solve(grid):
    """Crop the main rectangle and apply each outside (replacement, source) pair."""
    if not grid or not grid[0]:
        return []

    component = _largest_same_color_component(grid)
    if not component:
        return [list(row) for row in grid]

    top = min(row for row, _ in component)
    bottom = max(row for row, _ in component)
    left = min(col for _, col in component)
    right = max(col for _, col in component)

    def inside_bbox(row, col):
        return top <= row <= bottom and left <= col <= right

    mapping = {}
    width = len(grid[0])
    for row, values in enumerate(grid):
        col = 0
        while col < width:
            if values[col] == 0 or inside_bbox(row, col):
                col += 1
                continue
            start = col
            while (
                col < width
                and values[col] != 0
                and not inside_bbox(row, col)
            ):
                col += 1
            if col - start == 2:
                replacement, source = values[start], values[start + 1]
                mapping[source] = replacement

    return [
        [mapping.get(grid[row][col], grid[row][col]) for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
