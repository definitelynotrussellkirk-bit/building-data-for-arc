from collections import deque
from typing import Sequence

Grid = list[list[int]]


def _components(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    """Return four-connected non-background components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(cells)
    return components


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Color each nested rectangular frame by its containment depth.

    The outermost frame becomes 2, the frame immediately inside it becomes 3,
    and so on. Background cells remain zero.
    """
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    components = _components(grid)
    boxes: list[tuple[int, int, int, int]] = []
    for cells in components:
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        boxes.append((min(rows), min(cols), max(rows), max(cols)))

    output = [list(row) for row in grid]
    for index, cells in enumerate(components):
        top, left, bottom, right = boxes[index]
        depth = sum(
            other_top < top
            and other_left < left
            and other_bottom > bottom
            and other_right > right
            for other_index, (other_top, other_left, other_bottom, other_right) in enumerate(boxes)
            if other_index != index
        )
        for row, col in cells:
            output[row][col] = 2 + depth
    return output
