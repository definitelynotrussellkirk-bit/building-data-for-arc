"""Visible-example solution for Depth-Colored Nested Frames."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor nested color-1 frame components from outside to inside."""
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != 1 or (start_r, start_c) in seen:
                continue
            queue = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            for r, c in queue:
                cells.append((r, c))
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
            components.append(cells)

    def bounding_area(cells: list[tuple[int, int]]) -> int:
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)

    components.sort(key=bounding_area, reverse=True)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for depth, cells in enumerate(components, start=2):
        for r, c in cells:
            output[r][c] = depth
    return output
