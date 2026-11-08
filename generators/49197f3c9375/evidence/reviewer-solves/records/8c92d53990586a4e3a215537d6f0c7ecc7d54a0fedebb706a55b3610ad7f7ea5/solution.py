"""Visible-only solution for the prepared ARC episode."""
from __future__ import annotations

from collections import defaultdict, deque

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate90(cells):
    return _normalize((c, -r) for r, c in cells)


def _reflect(cells):
    return _normalize((r, -c) for r, c in cells)


def _signature(cells):
    shape = _normalize(cells)
    variants = []
    for reflected in (False, True):
        current = _reflect(shape) if reflected else shape
        for _ in range(4):
            variants.append(current)
            current = _rotate90(current)
    return min(variants)


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    out = []
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
                for dr, dc in _NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append((color, _normalize(cells)))
    return out


def solve(grid):
    components = _components(grid)
    by_signature = defaultdict(list)
    for color, shape in components:
        by_signature[_signature(shape)].append((color, shape))

    unmatched = [items[0] for items in by_signature.values() if len(items) == 1]
    if len(unmatched) != 1:
        raise ValueError("expected exactly one unmatched dihedral shape class")

    color, shape = unmatched[0]
    cells = set(shape)
    boundary = {
        (r, c)
        for r, c in cells
        if any((r + dr, c + dc) not in cells for dr, dc in _NEIGHBORS)
    }
    max_r = max(r for r, _ in cells)
    max_c = max(c for _, c in cells)
    output = [[0 for _ in range(max_c + 1)] for _ in range(max_r + 1)]
    for r, c in boundary:
        output[r][c] = color
    return output
