from collections import deque


DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in DIR4:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        yield component


def _fill_component_holes(source, result, color, component):
    top = min(row for row, _ in component)
    bottom = max(row for row, _ in component)
    left = min(col for _, col in component)
    right = max(col for _, col in component)

    zeros = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if source[row][col] == 0
    }
    exterior = set()
    queue = deque()
    for cell in zeros:
        row, col = cell
        if row in (top, bottom) or col in (left, right):
            exterior.add(cell)
            queue.append(cell)

    while queue:
        row, col = queue.popleft()
        for dr, dc in DIR4:
            nxt = (row + dr, col + dc)
            if nxt in zeros and nxt not in exterior:
                exterior.add(nxt)
                queue.append(nxt)

    for row, col in zeros - exterior:
        result[row][col] = color


def solve(grid):
    source = [row[:] for row in grid]
    result = [row[:] for row in grid]
    colors = sorted({cell for row in source for cell in row if cell != 0})
    for color in colors:
        for component in _components(source, color):
            _fill_component_holes(source, result, color, component)
    return result
