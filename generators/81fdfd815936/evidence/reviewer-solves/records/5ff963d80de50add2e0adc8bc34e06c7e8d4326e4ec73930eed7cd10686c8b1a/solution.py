"""Visible-example solution: crop the earliest left-right-symmetric object."""
from __future__ import annotations


def _components4(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return sorted(
        components,
        key=lambda component: (
            min(row for row, _ in component[1]),
            min(col for _, col in component[1]),
        ),
    )


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _left_right_symmetric(cells):
    row0, col0, _, col1 = _bbox(cells)
    normalized = {(row - row0, col - col0) for row, col in cells}
    width = col1 - col0 + 1
    return all((row, width - 1 - col) in normalized for row, col in normalized)


def solve(grid):
    """Return the tight crop of the first LR-symmetric object by (top,left)."""
    for _, cells in _components4(grid):
        if _left_right_symmetric(cells):
            row0, col0, row1, col1 = _bbox(cells)
            return [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]
    raise ValueError("no left-right-symmetric object")
