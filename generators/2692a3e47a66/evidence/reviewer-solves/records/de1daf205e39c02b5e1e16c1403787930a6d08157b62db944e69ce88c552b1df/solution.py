from collections import Counter, defaultdict, deque


def _components(grid, background):
    """Return 4-connected non-background components as coordinate lists."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            todo = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))

            components.append((color, cells))

    return components


def solve(grid):
    """Move repeated-color corner objects inward by their own dimensions."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    components = _components(grid, background)

    corner_components = []
    counts_by_color = defaultdict(int)
    for color, cells in components:
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        vertical = "top" if min_row == 0 else "bottom" if max_row == height - 1 else None
        horizontal = "left" if min_col == 0 else "right" if max_col == width - 1 else None
        if vertical is None or horizontal is None:
            continue

        item = {
            "color": color,
            "cells": cells,
            "min_row": min_row,
            "max_row": max_row,
            "min_col": min_col,
            "max_col": max_col,
            "vertical": vertical,
            "horizontal": horizontal,
        }
        corner_components.append(item)
        counts_by_color[color] += 1

    result = [row[:] for row in grid]
    for item in corner_components:
        if counts_by_color[item["color"]] < 2:
            continue

        object_height = item["max_row"] - item["min_row"] + 1
        object_width = item["max_col"] - item["min_col"] + 1
        row_shift = object_height if item["vertical"] == "top" else -object_height
        col_shift = object_width if item["horizontal"] == "left" else -object_width

        for row, col in item["cells"]:
            result[row][col] = background
        for row, col in item["cells"]:
            result[row + row_shift][col + col_shift] = item["color"]

    return result
