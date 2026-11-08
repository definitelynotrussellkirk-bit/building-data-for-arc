"""Visible-example solution for 147c2b92e5c1."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if not (1 <= nr < h and 0 <= nc < w):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            result.append(cells)
    return result


def _crop(grid, cells):
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    keep = set(cells)
    return [
        [grid[r][c] if (r, c) in keep else 0 for c in range(left, right + 1)]
        for r in range(top, bottom + 1)
    ]


def _holes(shape):
    h, w = len(shape), len(shape[0])
    zeros = {(r, c) for r in range(h) for c in range(w) if shape[r][c] == 0}
    seen = set()
    count = 0
    for start in zeros:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        edge = False
        while stack:
            r, c = stack.pop()
            edge = edge or r in (0, h - 1) or c in (0, w - 1)
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in zeros and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if not edge:
            count += 1
    return count


def _transform(shape, code):
    if code == 1:
        return [row[:] for row in shape]
    if code == 2:
        return [list(row) for row in zip(*shape[::-1])]
    if code == 3:
        return [row[::-1] for row in shape[::-1]]
    if code == 4:
        return [list(row) for row in zip(*shape)][::-1]
    if code == 5:
        return [row[::-1] for row in shape]
    if code == 6:
        return [row[:] for row in shape[::-1]]
    raise ValueError(f"unknown transform code: {code}")


def _scale2(shape):
    output = []
    for row in shape:
        doubled = [value for value in row for _ in range(2)]
        output.append(doubled[:])
        output.append(doubled[:])
    return output


def solve(grid):
    code_cells = [value for value in grid[0] if value != 0]
    if len(code_cells) != 1:
        raise ValueError("expected one transform code in row 0")
    candidates = []
    for cells in _components(grid):
        shape = _crop(grid, cells)
        if _holes(shape) == 1:
            candidates.append(shape)
    if len(candidates) != 1:
        raise ValueError("expected one one-hole body object")
    return _scale2(_transform(candidates[0], code_cells[0]))
