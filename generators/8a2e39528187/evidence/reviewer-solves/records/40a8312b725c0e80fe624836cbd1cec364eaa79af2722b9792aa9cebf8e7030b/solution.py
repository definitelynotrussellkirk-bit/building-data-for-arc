"""Visible-example solution for the prepared 8a2e39528187 episode."""
from __future__ import annotations

from collections import deque


DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
RANK_COLORS = (2, 4, 6, 8)


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return monochromatic nonzero 4-connected components."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in DIR4:
                    rr, cc = row + drow, col + dcol
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            result.append(cells)
    return result


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor four objects by ascending (area, bounding-box) rank."""
    if not grid or not grid[0]:
        return []
    components = sorted(_components(grid), key=lambda cells: (len(cells), _bbox(cells)))
    if len(components) != len(RANK_COLORS):
        raise ValueError(f"expected four objects, found {len(components)}")
    output = [[0 for _ in row] for row in grid]
    for cells, color in zip(components, RANK_COLORS):
        for row, col in cells:
            output[row][col] = color
    return output
