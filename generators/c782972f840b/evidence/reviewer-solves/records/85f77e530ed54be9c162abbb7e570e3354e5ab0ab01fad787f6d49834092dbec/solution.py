from __future__ import annotations


def _components(grid: list[list[int]]) -> list[tuple[int, tuple[tuple[int, ...], ...]]]:
    """Return non-background monochrome components in row-major discovery order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    objects: list[tuple[int, tuple[tuple[int, ...], ...]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            min_row = min(cell[0] for cell in cells)
            max_row = max(cell[0] for cell in cells)
            min_col = min(cell[1] for cell in cells)
            max_col = max(cell[1] for cell in cells)
            occupied = set(cells)
            shape = tuple(
                tuple(
                    1 if (shape_row, shape_col) in occupied else 0
                    for shape_col in range(min_col, max_col + 1)
                )
                for shape_row in range(min_row, max_row + 1)
            )
            objects.append((color, shape))

    return objects


def _rotate_clockwise(shape: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in zip(*shape[::-1]))


def _rotation_key(shape: tuple[tuple[int, ...], ...]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    rotations = []
    current = shape
    for _ in range(4):
        rotations.append(current)
        current = _rotate_clockwise(current)
    return min(rotations)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Encode pairwise object relations as a symmetric relation matrix.

    Diagonal entries are 9.  Off diagonal, add 2 when the two objects share a
    color and add 4 when their binary shapes match under rotation (not mirror).
    """
    objects = _components(grid)
    keys = [_rotation_key(shape) for _, shape in objects]
    size = len(objects)
    output = [[0 for _ in range(size)] for _ in range(size)]

    for left in range(size):
        output[left][left] = 9
        for right in range(left + 1, size):
            relation = 0
            if objects[left][0] == objects[right][0]:
                relation += 2
            if keys[left] == keys[right]:
                relation += 4
            output[left][right] = relation
            output[right][left] = relation

    return output
