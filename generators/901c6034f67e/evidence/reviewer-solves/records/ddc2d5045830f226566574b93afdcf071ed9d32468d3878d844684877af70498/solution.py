"""Visible-example solution for task 901c6034f67e."""

from collections import deque


_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _objects(grid):
    """Return monochrome 4-connected nonzero objects in row-major order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in _NEIGHBORS:
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            objects.append(tuple(sorted(cells)))
    return objects


def _contour_cell_count(cells):
    occupied = set(cells)
    return sum(
        any((row + dr, col + dc) not in occupied for dr, dc in _NEIGHBORS)
        for row, col in cells
    )


def solve(grid):
    """Rank objects by contour-cell count and recolor them 2, 3, 4, ..."""
    if not grid or not grid[0]:
        return []
    objects = _objects(grid)
    ranked = sorted(objects, key=lambda cells: (_contour_cell_count(cells), min(cells)))
    rank_colors = (2, 3, 4, 6, 7, 8, 9)
    output = [[0 for _ in row] for row in grid]
    for rank, cells in enumerate(ranked):
        color = rank_colors[rank]
        for row, col in cells:
            output[row][col] = color
    return output
