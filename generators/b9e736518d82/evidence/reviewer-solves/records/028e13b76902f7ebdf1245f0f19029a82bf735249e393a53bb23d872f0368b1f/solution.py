"""Visible-example solution for the repaired zigzag-channel task."""
from collections import deque
from copy import deepcopy

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _neighbors(point):
    r, c = point
    for dr, dc in CARDINAL:
        yield r + dr, c + dc


def _component(start, pool):
    seen = {start}
    queue = deque([start])
    while queue:
        point = queue.popleft()
        for nxt in _neighbors(point):
            if nxt in pool and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def solve(grid):
    h, w = len(grid), len(grid[0])
    band = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (0, 9):
                continue
            if any(
                0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 7
                for nr, nc in _neighbors((r, c))
            ):
                band.append((r, c))

    pool = set(band)
    marker = next((point for point in band if grid[point[0]][point[1]] == 9), None)
    if marker is not None:
        channel = _component(marker, pool)
    else:
        first = _component(band[0], pool)
        remaining = [point for point in band if point not in first]
        if not remaining:
            channel = first
        else:
            second = _component(remaining[0], pool)
            channel = first if len(first) > len(second) else second

    if marker is None:
        fill = channel
    else:
        neighbors = [point for point in _neighbors(marker) if point in channel]
        straight = (
            all(r == marker[0] for r, _ in neighbors)
            or all(c == marker[1] for _, c in neighbors)
        )
        if straight:
            fill = channel
        else:
            without_marker = channel - {marker}
            first_half = _component(min(without_marker), without_marker)
            second_half = without_marker - first_half
            fill = first_half if len(first_half) > len(second_half) else second_half

    output = deepcopy(grid)
    for r, c in fill:
        output[r][c] = 8
    return output
