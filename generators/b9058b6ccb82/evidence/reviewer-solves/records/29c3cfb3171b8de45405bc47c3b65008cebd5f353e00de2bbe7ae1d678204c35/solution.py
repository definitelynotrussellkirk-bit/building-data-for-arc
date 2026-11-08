from collections import Counter


def _normalize(cells):
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate(cells):
    cells = _normalize(cells)
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def _reflect(cells):
    cells = _normalize(cells)
    width = max(c for _, c in cells) + 1
    return _normalize((r, width - 1 - c) for r, c in cells)


def _canonical(cells):
    variants = []
    for start in (_normalize(cells), _reflect(cells)):
        current = start
        for _ in range(4):
            variants.append(_normalize(current))
            current = _rotate(current)
    return min(variants)


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
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
                        stack.append((nr, nc))
            result.append({"color": color, "cells": cells, "shape": _canonical(cells)})
    return result


def solve(grid):
    """Return the uniquely shaped colored object, cropped in its observed pose."""
    objects = _components(grid)
    frequencies = Counter(obj["shape"] for obj in objects)
    candidates = [obj for obj in objects if frequencies[obj["shape"]] == 1]
    if len(candidates) != 1:
        raise ValueError(f"expected one unique dihedral shape, found {len(candidates)}")

    target = candidates[0]
    rows = [r for r, _ in target["cells"]]
    cols = [c for _, c in target["cells"]]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)
    output = [[0 for _ in range(max_c - min_c + 1)] for _ in range(max_r - min_r + 1)]
    for r, c in target["cells"]:
        output[r - min_r][c - min_c] = target["color"]
    return output
