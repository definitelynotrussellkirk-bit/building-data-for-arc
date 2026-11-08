"""Visible-example solution for the generated ARC lesson."""
from __future__ import annotations


def _components8(grid):
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
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append(cells)
    return components


def _is_left_right_symmetric(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    normalized = {(row - row0, col - col0) for row, col in cells}
    width = max(col for _, col in normalized) + 1
    return all((row, width - 1 - col) in normalized for row, col in normalized)


def solve(grid):
    """Crop the unique 8-connected object that lacks left-right symmetry."""
    components = _components8(grid)
    asymmetric = [cells for cells in components if not _is_left_right_symmetric(cells)]
    if len(asymmetric) != 1:
        raise ValueError(f"expected one asymmetric object, found {len(asymmetric)}")
    cells = asymmetric[0]
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [row[col0:col1 + 1] for row in grid[row0:row1 + 1]]
