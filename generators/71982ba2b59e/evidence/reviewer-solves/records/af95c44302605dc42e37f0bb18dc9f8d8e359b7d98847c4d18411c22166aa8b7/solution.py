from collections import deque


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform(cells, rotation, reflected):
    transformed = []
    for r, c in cells:
        if reflected:
            c = -c
        for _ in range(rotation):
            r, c = c, -r
        transformed.append((r, c))
    return _normalize(transformed)


def _shape_key(cells):
    normalized = _normalize(cells)
    return min(
        _transform(normalized, rotation, reflected)
        for reflected in (False, True)
        for rotation in range(4)
    )


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
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
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            objects.append(
                {
                    "colour": colour,
                    "cells": cells,
                    "anchor": (min(r for r, _ in cells), min(c for _, c in cells)),
                    "shape": _shape_key(cells),
                }
            )

    objects.sort(key=lambda obj: obj["anchor"])
    return objects


def solve(grid):
    objects = _components(grid)
    size = len(objects)
    output = [[0 for _ in range(size)] for _ in range(size)]

    for i, left in enumerate(objects):
        output[i][i] = left["colour"]
        for j in range(i + 1, size):
            right = objects[j]
            if left["shape"] == right["shape"]:
                relation = 8
            elif left["colour"] == right["colour"]:
                relation = 6
            else:
                relation = 0
            output[i][j] = relation
            output[j][i] = relation

    return output
