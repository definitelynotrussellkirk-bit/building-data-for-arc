"""Visible-example solution for ARC task f705b8f51e62.

The input contains several separated non-background objects.  One normalized
shape is repeated; a single different object supplies the output color.  Return
one tightly cropped copy of the repeated shape, recolored with the odd object's
color (which may equal the repeated objects' color).
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Iterable

Grid = list[list[int]]
Shape = tuple[tuple[int, ...], ...]


def _components(grid: Grid) -> list[list[tuple[int, int]]]:
    """Return 4-connected nonzero components in reading order."""
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _shape(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = list(cells)
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)
    occupied = set(cells)
    return tuple(
        tuple(
            1 if (row, col) in occupied else 0
            for col in range(min_col, max_col + 1)
        )
        for row in range(min_row, max_row + 1)
    )


def _component_color(grid: Grid, cells: list[tuple[int, int]]) -> int:
    """Use the component's dominant color; generated examples are monochrome."""
    return Counter(grid[row][col] for row, col in cells).most_common(1)[0][0]


def solve(grid: Grid) -> Grid:
    components = _components(grid)
    if not components:
        return []

    by_shape: dict[Shape, list[int]] = defaultdict(list)
    shapes: list[Shape] = []
    colors: list[int] = []
    for index, cells in enumerate(components):
        shape = _shape(cells)
        shapes.append(shape)
        colors.append(_component_color(grid, cells))
        by_shape[shape].append(index)

    repeated_shape, repeated_indices = max(
        by_shape.items(),
        key=lambda item: (len(item[1]), sum(sum(row) for row in item[0])),
    )

    repeated_set = set(repeated_indices)
    odd_indices = [index for index in range(len(components)) if index not in repeated_set]
    output_color = colors[odd_indices[0]] if odd_indices else colors[repeated_indices[0]]

    return [
        [output_color if occupied else 0 for occupied in row]
        for row in repeated_shape
    ]
