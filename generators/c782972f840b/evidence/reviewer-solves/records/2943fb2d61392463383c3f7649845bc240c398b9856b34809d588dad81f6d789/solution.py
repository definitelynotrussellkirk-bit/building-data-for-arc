"""Visible-example solution for c782972f840b."""
from __future__ import annotations


def _normalize(points):
    points = tuple(points)
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return tuple(sorted((row - top, col - left) for row, col in points))


def _rotate(shape):
    return _normalize((col, -row) for row, col in shape)


def _rotation_key(shape):
    current = _normalize(shape)
    variants = []
    for _ in range(4):
        variants.append(current)
        current = _rotate(current)
    return min(variants)


def _objects(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = row + drow, col + dcol
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 0
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            top_left = (min(row for row, _ in cells), min(col for _, col in cells))
            colors = {grid[row][col] for row, col in cells}
            if len(colors) != 1:
                raise ValueError("expected monochrome objects")
            found.append(
                {
                    "top_left": top_left,
                    "color": next(iter(colors)),
                    "shape": _rotation_key(cells),
                }
            )
    return sorted(found, key=lambda item: item["top_left"])


def solve(grid):
    items = _objects(grid)
    size = len(items)
    output = [[0] * size for _ in range(size)]
    for row, left in enumerate(items):
        for col, right in enumerate(items):
            if row == col:
                output[row][col] = 9
                continue
            same_shape = left["shape"] == right["shape"]
            same_color = left["color"] == right["color"]
            output[row][col] = (
                6
                if same_shape and same_color
                else 4
                if same_shape
                else 2
                if same_color
                else 0
            )
    return output
