from __future__ import annotations


def _normalize(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return sorted((row - min_row, col - min_col) for row, col in cells)


def _components(grid, allowed):
    unseen = set(allowed)
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append((color, component))
    return result


def _rotate(shape, code):
    shape = _normalize(shape)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    if code == 2:
        transformed = shape
    elif code == 3:  # 90 degrees clockwise
        transformed = [(col, height - 1 - row) for row, col in shape]
    elif code == 4:  # 180 degrees
        transformed = [
            (height - 1 - row, width - 1 - col) for row, col in shape
        ]
    else:  # code 5: 90 degrees counter-clockwise
        transformed = [(width - 1 - col, row) for row, col in shape]
    return _normalize(transformed)


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    anchors = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in {2, 3, 4, 5}
    ]
    ordinary = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in {0, 2, 3, 4, 5}
    }
    components = _components(grid, ordinary)
    prototype_color, prototype_cells = max(components, key=lambda item: len(item[1]))
    shape = _normalize(prototype_cells)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for anchor_row, anchor_col, code in anchors:
        for dr, dc in _rotate(shape, code):
            row = anchor_row + dr
            col = anchor_col + dc
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = prototype_color
    return output
