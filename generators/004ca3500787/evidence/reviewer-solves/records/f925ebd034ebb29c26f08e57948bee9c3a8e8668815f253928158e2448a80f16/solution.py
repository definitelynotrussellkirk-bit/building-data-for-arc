"""Standalone solution written during the final visible-example solve."""

from collections import Counter


def _shape_key(cells):
    poses = []
    for swap in (False, True):
        for row_sign in (-1, 1):
            for col_sign in (-1, 1):
                pose = [
                    (row_sign * (c if swap else r),
                     col_sign * (r if swap else c))
                    for r, c in cells
                ]
                top = min(r for r, _ in pose)
                left = min(c for _, c in pose)
                poses.append(tuple(sorted((r - top, c - left) for r, c in pose)))
    return min(poses)


def solve(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }
    keys = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        frontier = [start]
        while frontier:
            r, c = frontier.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        keys.append(_shape_key(component))
    frequencies = Counter(keys)
    singletons = [key for key, count in frequencies.items() if count == 1]
    if len(singletons) != 1:
        raise ValueError("Expected exactly one shape class occurring once")
    target = singletons[0]
    height = 1 + max(r for r, _ in target)
    width = 1 + max(c for _, c in target)
    result = [[0] * width for _ in range(height)]
    for r, c in target:
        result[r][c] = 8
    return result
