"""Visible-example solver for the exposed ee6a99e8b7f9 episode."""
from collections import deque
from copy import deepcopy

CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] in (5, 6)}
    shapes = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
                    cells.add(point)
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        shapes.append((color, (r1, c1, r2, c2), cells))
    return sorted(shapes, key=lambda item: item[1])


def _side(dot, box):
    r, c = dot
    r1, c1, r2, c2 = box
    if r1 <= r <= r2 and c == c1 - 1:
        return "left"
    if r1 <= r <= r2 and c == c2 + 1:
        return "right"
    if c1 <= c <= c2 and r == r1 - 1:
        return "above"
    if c1 <= c <= c2 and r == r2 + 1:
        return "below"
    return None


def solve(grid):
    shapes = _components(grid)
    output = deepcopy(grid)

    # Gray rectangles disappear before marker destinations are painted.
    for color, _box, cells in shapes:
        if color == 5:
            for r, c in cells:
                output[r][c] = 8

    dots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    for dot in dots:
        hits = []
        for color, box, _cells in shapes:
            side = _side(dot, box)
            if side is not None:
                hits.append((color, box, side))
        if len(hits) != 1:
            continue
        color, (r1, c1, r2, c2), side = hits[0]
        r, c = dot
        if color == 6:
            output[r][c] = 8
            if side in ("left", "right"):
                target = (r, (c1 + c2) // 2)
            else:
                target = ((r1 + r2) // 2, c)
        else:
            target = {
                "left": (r, c1),
                "right": (r, c2),
                "above": (r1, c),
                "below": (r2, c),
            }[side]
        output[target[0]][target[1]] = 9
    return output
