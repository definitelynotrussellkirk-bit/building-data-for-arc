"""Visible-example solution for task 697e51dfedef."""

from collections import deque


def solve(grid):
    """Recolor the three nonzero 4-connected objects by increasing area.

    Smallest -> 2, middle -> 4, largest -> 8.  Shape and location stay fixed.
    Components are color-preserving because each visible object has one source color.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
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
            objects.append(cells)

    ranked = sorted(objects, key=len)
    if len(ranked) != 3 or len({len(cells) for cells in ranked}) != 3:
        raise ValueError("expected exactly three objects with distinct areas")

    answer = [row[:] for row in grid]
    for cells, new_color in zip(ranked, (2, 4, 8)):
        for row, col in cells:
            answer[row][col] = new_color
    return answer
