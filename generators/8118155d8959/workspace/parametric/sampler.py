"""Setting-independent connected-shape scenes for the proposed ranking family."""
from __future__ import annotations

import hashlib
import random


def rng_for(seed, *parts):
    key = ":".join(map(str, ("8118155d8959-input-v1", seed, *parts)))
    return random.Random(hashlib.sha256(key.encode()).digest())


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def orient(cells, code):
    points = list(cells)
    if code >= 4:
        points = [(r, -c) for r, c in points]
    for _ in range(code % 4):
        points = [(c, -r) for r, c in points]
    return normalize(points)


def rotate_grid(grid, code):
    result = [list(row) for row in grid]
    if code >= 4:
        result = [row[::-1] for row in result]
    for _ in range(code % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def lanes(width):
    usable = width - 2
    widths = [usable // 3 + (i < usable % 3) for i in range(3)]
    starts = [0, widths[0] + 1, widths[0] + widths[1] + 2]
    return list(zip(starts, widths))


def polyomino(rng, height, width, count):
    # A connected backbone spans the whole chosen bounding box. Frontier growth
    # produces sparse elongated and dense irregular shapes on that backbone.
    choices = [(h, w) for h in range(2, height + 1)
               for w in range(2, width + 1) if h + w - 1 <= count <= h * w]
    h, w = rng.choice(choices)
    cells = {(r, 0) for r in range(h)} | {(0, c) for c in range(w)}
    frontier = set()
    for r, c in cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (r + dr, c + dc)
            if 0 <= p[0] < h and 0 <= p[1] < w and p not in cells:
                frontier.add(p)
    while len(cells) < count:
        p = rng.choice(sorted(frontier))
        frontier.remove(p)
        cells.add(p)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (p[0] + dr, p[1] + dc)
            if 0 <= q[0] < h and 0 <= q[1] < w and q not in cells:
                frontier.add(q)
    if rng.randrange(2):
        cells = {(h - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, w - 1 - c) for r, c in cells}
    return tuple(sorted(cells))


def distractors(grid, rng):
    height, width = len(grid), len(grid[0])
    for color in (5, 6, 7, 9):
        free = [(r, c) for r in range(height) for c in range(width)
                if grid[r][c] == 0]
        if not free:
            break
        start = rng.choice(free)
        cells, frontier = set(), {start}
        count = rng.randint(2, max(3, height * width // 80))
        while frontier and len(cells) < count:
            p = rng.choice(sorted(frontier))
            frontier.remove(p)
            cells.add(p)
            grid[p[0]][p[1]] = color
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + dr, p[1] + dc)
                if (0 <= q[0] < height and 0 <= q[1] < width
                        and grid[q[0]][q[1]] == 0 and q not in cells):
                    frontier.add(q)


def sample_input(seed, *, index, height, width):
    integer(seed, "seed", 0, 2**63 - 1)
    integer(index, "index", 0, 2**31 - 1)
    integer(height, "height", 10, 30)
    integer(width, "width", 10, 30)
    rng = rng_for(seed, "scene", index, height, width)
    code = rng.randrange(8)
    h, w = (width, height) if code % 2 else (height, width)
    slots = lanes(w)
    capacity = h * min(size for _, size in slots)
    low, high = max(4, (capacity + 5) // 6), max(7, 3 * capacity // 4)
    counts = rng.sample(range(low, high + 1), 3)
    grid = [[0] * w for _ in range(h)]
    for i, ((left, lane_width), count) in enumerate(zip(slots, counts)):
        cells = polyomino(rng, h, lane_width, count)
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        row = 0 if i == 0 else h - sh if i == 1 else rng.randrange(h - sh + 1)
        col = left if i == 0 else left + lane_width - sw if i == 2 else left + rng.randrange(lane_width - sw + 1)
        for dr, dc in cells:
            grid[row + dr][col + dc] = 1
    distractors(grid, rng)
    return rotate_grid(grid, code)


def teaching_input(seed, index, attempt=0):
    """Teach metric, row/column ties, and changing T4 ranks in two examples.

    First: T4(4/6) is above/right of rectangle6(6/6); L5(5/8) is
    intermediate by cells but last by area. Second: P5(5/6) and T4(4/6)
    share a top row, with P5 to the left; L3(3/4) is the smallest. These
    opposite size/tie correlations refute cell-count tie shortcuts as well.
    """
    rng = rng_for(seed, "teaching", index, attempt)
    t4 = ((0, 0), (0, 1), (0, 2), (1, 1))
    grid = [[0] * 12 for _ in range(12)]
    def place(shape, row, col, codes=range(8)):
        cells = orient(shape, rng.choice(tuple(codes)))
        for dr, dc in cells:
            if grid[row + dr][col + dc] != 0:
                raise ValueError("teaching shape collision")
            grid[row + dr][col + dc] = 1
    if index == 0:
        rectangle6 = tuple((r, c) for r in range(2) for c in range(3))
        l5 = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0))
        place(t4, rng.randrange(3), rng.randint(7, 9))
        place(rectangle6, rng.randint(6, 8), rng.randrange(3))
        place(l5, rng.randint(9, 10), rng.randint(7, 8), codes=(0, 2, 4, 6))
    else:
        p5 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1))
        l3 = ((0, 0), (1, 0), (1, 1))
        top = rng.randrange(3)
        place(p5, top, rng.randrange(3))
        place(t4, top, rng.randint(7, 9))
        place(l3, rng.randint(9, 10), rng.randint(5, 7))
    distractors(grid, rng)
    return grid
