def _components_below(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] == color
    }
    result = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(cells)
    return result


def _crop(grid, cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [list(row[c1:c2 + 1]) for row in grid[r1:r2 + 1]]


def solve(grid):
    """Pack the largest body component of each top-row color in legend order."""
    legend = [value for value in grid[0] if value != 0]
    blocks = []
    for color in legend:
        components = _components_below(grid, color)
        chosen = min(
            components,
            key=lambda cells: (
                -len(cells),
                min(r for r, _ in cells),
                min(c for _, c in cells),
            ),
        )
        blocks.append(_crop(grid, chosen))

    height = max(len(block) for block in blocks)
    width = sum(len(block[0]) for block in blocks) + len(blocks) - 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    left = 0
    for block in blocks:
        for r, row in enumerate(block):
            for c, value in enumerate(row):
                if value != 0:
                    output[r][left + c] = value
        left += len(block[0]) + 1
    return output
