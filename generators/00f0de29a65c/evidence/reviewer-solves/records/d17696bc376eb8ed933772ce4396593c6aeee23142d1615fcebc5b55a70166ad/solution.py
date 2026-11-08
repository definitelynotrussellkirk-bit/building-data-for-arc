from collections import deque

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
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
                for drow, dcol in DIR4:
                    nr, nc = row + drow, col + dcol
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            found.append(
                {
                    "color": color,
                    "cells": set(cells),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return found


def solve(grid):
    objects = components(grid)
    marker = next(obj for obj in objects if obj["size"] == 1)
    shapes = [obj for obj in objects if obj["size"] > 1]
    target = min(
        shapes,
        key=lambda obj: (obj["size"], obj["bbox"][0], obj["bbox"][1]),
    )

    row1, col1, row2, col2 = target["bbox"]
    cropped = [
        [marker["color"] if (row, col) in target["cells"] else 0 for col in range(col1, col2 + 1)]
        for row in range(row1, row2 + 1)
    ]
    result = []
    for row in cropped:
        doubled = [value for value in row for _ in range(2)]
        result.extend([doubled[:], doubled[:]])
    return result
