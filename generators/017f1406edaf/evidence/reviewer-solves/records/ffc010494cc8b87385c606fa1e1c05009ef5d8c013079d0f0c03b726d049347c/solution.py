"""Visible-example solution for task 017f1406edaf."""
from __future__ import annotations


def _components(grid):
    """Yield nonzero monochrome 4-connected components in row-major order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            yield color, cells


def solve(grid):
    """Paint the eligible object whose area equals the top-row blue count."""
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    target_size = sum(value == 1 for value in grid[0])
    output = [[0 for _ in row] for row in grid]

    for color, cells in _components(grid):
        if color == 1 or any(row == 0 for row, _ in cells):
            continue
        if len(cells) == target_size:
            for row, col in cells:
                output[row][col] = 8
            break
    return output
