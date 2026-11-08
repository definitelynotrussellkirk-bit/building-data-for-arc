from collections import deque


def _components(grid, colour=1):
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == colour
    }
    found = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for point in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    queue.append(point)
        found.append(cells)
    return found


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_exact_frame(cells):
    top, left, bottom, right = _bbox(cells)
    if bottom - top + 1 < 3 or right - left + 1 < 3:
        return False
    border = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }
    return cells == border


def solve(grid):
    palette = [value for value in grid[0] if value != 0]
    body = [row[:] for row in grid[1:]]
    output = [[0 for _ in row] for row in body]

    frames = [cells for cells in _components(body) if _is_exact_frame(cells)]
    frames.sort(
        key=lambda cells: -(
            (_bbox(cells)[2] - _bbox(cells)[0] + 1)
            * (_bbox(cells)[3] - _bbox(cells)[1] + 1)
        )
    )
    for depth, cells in enumerate(frames):
        colour = palette[min(depth, len(palette) - 1)]
        for row, col in cells:
            output[row][col] = colour
    return output
