"""Visible-example solution for task 1cbcf1ed9a32."""

from collections import Counter, deque
from typing import Iterable

Grid = list[list[int]]
Point = tuple[int, int]
Shape = tuple[Point, ...]


def _normalize(points: Iterable[Point]) -> Shape:
    points = tuple(points)
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _canonical(points: Iterable[Point]) -> Shape:
    base = tuple(points)
    variants: list[Shape] = []
    for reflected in (False, True):
        transformed = [(row, -col if reflected else col) for row, col in base]
        for turns in range(4):
            current: list[Point] = []
            for row, col in transformed:
                for _ in range(turns):
                    row, col = col, -row
                current.append((row, col))
            variants.append(_normalize(current))
    return min(variants)


def _components(panel: Grid) -> list[Shape]:
    height = len(panel)
    width = len(panel[0])
    seen: set[Point] = set()
    result: list[Shape] = []
    for row in range(height):
        for col in range(width):
            if panel[row][col] == 0 or (row, col) in seen:
                continue
            color = panel[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[Point] = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and panel[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(_normalize(cells))
    return result


def _render(shape: Shape) -> Grid:
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    output = [[0] * width for _ in range(height)]
    for row, col in shape:
        output[row][col] = 8
    return output


def solve(grid: Grid) -> Grid:
    """Return the D4-canonical largest shape shared by two of three panels."""
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    dividers = [
        col
        for col in range(width)
        if all(row[col] == 5 for row in grid)
    ]
    if len(dividers) != 2:
        raise ValueError("expected exactly two full-height color-5 dividers")

    bounds = ((0, dividers[0]), (dividers[0] + 1, dividers[1]), (dividers[1] + 1, width))
    signatures: list[Shape] = []
    for start, stop in bounds:
        panel = [row[start:stop] for row in grid]
        components = _components(panel)
        if not components:
            raise ValueError("each panel must contain an object")
        largest_size = max(map(len, components))
        largest = [shape for shape in components if len(shape) == largest_size]
        if len(largest) != 1:
            raise ValueError("each panel must have a unique largest object")
        signatures.append(_canonical(largest[0]))

    counts = Counter(signatures)
    repeated = [shape for shape, count in counts.items() if count == 2]
    if len(repeated) != 1:
        raise ValueError("expected exactly one shape shared by two panels")
    return _render(repeated[0])
