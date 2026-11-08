def _components(grid, color):
    height, width = len(grid), len(grid[0])
    pending = {(r, c) for r in range(height) for c in range(width)
               if grid[r][c] == color}
    found = []
    while pending:
        start = min(pending)
        pending.remove(start)
        component, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in pending:
                    pending.remove(cell)
                    component.add(cell)
                    stack.append(cell)
        found.append(component)
    return found


def _normalized(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def solve(grid):
    output = [[0 for _ in row] for row in grid]
    rotations = set()
    for template in _components(grid, 1):
        shape = template
        for _ in range(4):
            rotations.add(_normalized(shape))
            shape = {(c, -r) for r, c in shape}
    for candidate in _components(grid, 3):
        if _normalized(candidate) in rotations:
            for r, c in candidate:
                output[r][c] = 8
    return output
