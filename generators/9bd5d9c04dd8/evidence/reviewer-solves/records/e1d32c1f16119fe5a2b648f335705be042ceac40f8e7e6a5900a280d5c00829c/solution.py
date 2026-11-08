"""Visible-example solver for task 9bd5d9c04dd8."""

from collections import deque
from typing import List, Sequence, Tuple

Grid = List[List[int]]


def _nonzero_components(grid: Sequence[Sequence[int]]) -> list[list[Tuple[int, int]]]:
    """Return 4-connected components of non-background cells."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    seen: set[Tuple[int, int]] = set()
    components: list[list[Tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component: list[Tuple[int, int]] = []
            while queue:
                cur_row, cur_col = queue.popleft()
                component.append((cur_row, cur_col))
                for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = cur_row + d_row
                    next_col = cur_col + d_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 0 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(component)
    return components


def solve(grid: Grid) -> Grid:
    """Extract the isolated 3x3 tile with the largest count of color 1."""
    candidates: list[Tuple[int, int, int, Grid]] = []
    for component in _nonzero_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if len(component) != 9 or bottom - top != 2 or right - left != 2:
            continue
        tile = [list(grid[row][left : right + 1]) for row in range(top, bottom + 1)]
        if any(value == 0 for tile_row in tile for value in tile_row):
            continue
        score = sum(value == 1 for tile_row in tile for value in tile_row)
        candidates.append((score, -top, -left, tile))

    if not candidates:
        raise ValueError("input contains no isolated filled 3x3 tile")

    # max() preserves the intended score ordering; negative coordinates make
    # row-major first win the otherwise unobserved tie case.
    return max(candidates, key=lambda item: item[:3])[3]
