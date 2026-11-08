"""Visible-example solver for task 4179e1ac3cf7."""
from __future__ import annotations


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            component = []
            while pending:
                r, c = pending.pop()
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
                        pending.append((nr, nc))
            result.append(component)
    return result


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def solve(grid):
    """Return the blank-grid mirror completion of exact green template copies."""
    templates = _components(grid, 1)
    if len(templates) != 1:
        raise ValueError(f"expected one color-1 template component, found {len(templates)}")
    target = _normalize(templates[0])
    output = [[0 for _ in row] for row in grid]
    for component in _components(grid, 3):
        if _normalize(component) != target:
            continue
        left = min(col for _, col in component)
        right = max(col for _, col in component)
        for row, col in component:
            output[row][col] = 8
            output[row][left + right - col] = 8
    return output
