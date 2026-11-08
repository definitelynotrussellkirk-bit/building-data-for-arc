from collections import Counter, deque


def _components(grid, color):
    """Return 4-connected interior components of ``color`` as coordinate sets."""
    height = len(grid)
    width = len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(1, width - 1)
        if grid[row][col] == color
    }
    parts = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        part = {start}
        while queue:
            row, col = queue.popleft()
            for nxt in ((row - 1, col), (row + 1, col),
                        (row, col - 1), (row, col + 1)):
                if nxt in unseen:
                    unseen.remove(nxt)
                    part.add(nxt)
                    queue.append(nxt)
        parts.append(part)
    return parts


def _slide(parts, width, direction):
    """Slide rigid components one column at a time toward a matching side."""
    if direction < 0:
        ordered = sorted(parts, key=lambda p: (min(c for _, c in p),
                                                min(r for r, _ in p)))
    else:
        ordered = sorted(parts, key=lambda p: (-max(c for _, c in p),
                                                min(r for r, _ in p)))

    occupied = set()
    result = []
    for part in ordered:
        current = set(part)
        while True:
            candidate = {(row, col + direction) for row, col in current}
            if any(col < 1 or col > width - 2 for _, col in candidate):
                break
            if candidate & occupied:
                break
            current = candidate
        occupied.update(current)
        result.append(current)
    return result


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    left_color = grid[0][0]
    right_color = grid[0][-1]

    interior = [
        grid[row][col]
        for row in range(height)
        for col in range(1, width - 1)
        if grid[row][col] not in (left_color, right_color)
    ]
    background = Counter(interior).most_common(1)[0][0]

    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(1, width - 1):
            if output[row][col] in (left_color, right_color):
                output[row][col] = background

    for part in _slide(_components(grid, left_color), width, -1):
        for row, col in part:
            output[row][col] = left_color

    for part in _slide(_components(grid, right_color), width, +1):
        for row, col in part:
            output[row][col] = right_color

    return output
