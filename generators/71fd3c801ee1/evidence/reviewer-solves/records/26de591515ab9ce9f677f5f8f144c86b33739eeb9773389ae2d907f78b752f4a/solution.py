"""Visible-example solver for the review solve episode."""
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

Grid = list[list[int]]
Cells = tuple[tuple[int, int], ...]


def _components(grid: Grid) -> list[tuple[int, Cells]]:
    """Return 4-connected, same-color, nonzero components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, Cells]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            cells: list[tuple[int, int]] = []
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
            result.append((color, tuple(cells)))
    return result


def _normalise(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return {(row - min_row, col - min_col) for row, col in cells}


def _feature(cells: Cells) -> tuple[int, int, int]:
    """Compute (area, enclosed-hole count, reflection-symmetry class)."""
    shape = _normalise(cells)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1

    # Count zero regions inside the bounding box that do not touch its edge.
    background = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in shape
    }
    visited: set[tuple[int, int]] = set()
    holes = 0
    for start in background:
        if start in visited:
            continue
        visited.add(start)
        queue = deque([start])
        touches_edge = False
        while queue:
            row, col = queue.popleft()
            if row in (0, height - 1) or col in (0, width - 1):
                touches_edge = True
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in background and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        if not touches_edge:
            holes += 1

    row_symmetric = all((height - 1 - row, col) in shape for row, col in shape)
    col_symmetric = all((row, width - 1 - col) in shape for row, col in shape)
    symmetry = (
        3
        if row_symmetric and col_symmetric
        else 1
        if row_symmetric
        else 2
        if col_symmetric
        else 0
    )
    return (len(shape), holes, symmetry)


def solve(grid: Grid) -> Grid:
    """Recolor to 8 every object whose complete feature triple repeats."""
    components = _components(grid)
    features = [_feature(cells) for _, cells in components]
    counts = Counter(features)
    output = [row[:] for row in grid]
    for (_, cells), feature in zip(components, features):
        if counts[feature] > 1:
            for row, col in cells:
                output[row][col] = 8
    return output


transform = solve
