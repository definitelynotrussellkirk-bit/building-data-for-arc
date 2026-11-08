"""Visible-example solution for fea6a4ce763f."""
from __future__ import annotations


def solve(grid):
    """Crop the uniquely largest non-zero monochromatic 4-connected component."""
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    seen = set()
    components = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)

    if not components:
        raise ValueError("grid has no foreground component")
    largest_size = max(map(len, components))
    largest = [cells for cells in components if len(cells) == largest_size]
    if len(largest) != 1:
        raise ValueError("largest component is not unique")

    cells = largest[0]
    row_min = min(row for row, _ in cells)
    row_max = max(row for row, _ in cells)
    col_min = min(col for _, col in cells)
    col_max = max(col for _, col in cells)
    return [row[col_min : col_max + 1] for row in grid[row_min : row_max + 1]]
