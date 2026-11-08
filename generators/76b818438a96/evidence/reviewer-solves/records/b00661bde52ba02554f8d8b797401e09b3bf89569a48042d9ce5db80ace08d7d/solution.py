"""Visible-example solution for task 76b818438a96."""
from __future__ import annotations

from collections import deque


def _neighbors(r: int, c: int, h: int, w: int):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                p = q.popleft()
                cells.append(p)
                for n in _neighbors(*p, h, w):
                    if n not in seen and grid[n[0]][n[1]] == color:
                        seen.add(n)
                        q.append(n)
            result.append((color, set(cells)))
    return result


def _path_order(cells, h, w, start):
    """Return the unique simple-path order beginning at endpoint start."""
    order = []
    previous = None
    current = start
    while True:
        order.append(current)
        choices = [
            n for n in _neighbors(*current, h, w)
            if n in cells and n != previous
        ]
        if not choices:
            return order
        previous, current = current, choices[0]


def solve(grid):
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    components = _components(grid)
    markers = [(color, next(iter(cells))) for color, cells in components if len(cells) == 1]
    paths = [(color, cells) for color, cells in components if len(cells) > 1]

    for path_color, cells in paths:
        endpoints = [
            p for p in cells
            if sum(n in cells for n in _neighbors(*p, h, w)) == 1
        ]
        if len(endpoints) != 2:
            continue

        match = None
        for endpoint in endpoints:
            neighbor = next(n for n in _neighbors(*endpoint, h, w) if n in cells)
            dr = endpoint[0] - neighbor[0]
            dc = endpoint[1] - neighbor[1]
            for marker_color, marker in markers:
                rr, cc = endpoint[0] + dr, endpoint[1] + dc
                gap = 0
                while 0 <= rr < h and 0 <= cc < w:
                    if (rr, cc) == marker:
                        match = endpoint, marker_color, marker, dr, dc, gap
                        break
                    if grid[rr][cc] != 0:
                        break
                    gap += 1
                    rr += dr
                    cc += dc
                if match is not None:
                    break
            if match is not None:
                break

        if match is None:
            continue

        aligned_endpoint, marker_color, marker, dr, dc, gap = match

        # Bridge the aligned endpoint to (but not over) the marker.
        rr, cc = aligned_endpoint[0] + dr, aligned_endpoint[1] + dc
        for _ in range(gap):
            out[rr][cc] = path_color
            rr += dr
            cc += dc

        # Paint the same number of cells inward from the opposite endpoint.
        opposite = endpoints[1] if endpoints[0] == aligned_endpoint else endpoints[0]
        inward = _path_order(cells, h, w, opposite)
        for r, c in inward[:gap]:
            out[r][c] = marker_color

    return out
