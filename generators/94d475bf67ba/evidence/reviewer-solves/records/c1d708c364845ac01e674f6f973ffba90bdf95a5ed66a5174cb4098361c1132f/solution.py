from copy import deepcopy


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def _frame(component):
    top = min(r for r, _ in component)
    left = min(c for _, c in component)
    bottom = max(r for r, _ in component)
    right = max(c for _, c in component)
    if bottom - top + 1 < 3 or right - left + 1 < 3:
        return None
    outline = (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )
    return (top, left, bottom, right) if component == outline else None


def solve(grid):
    """Fill each zero with its smallest enclosing exact rectangular frame color."""
    output = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    frames = []
    for color in colors:
        for component in _components(grid, color):
            box = _frame(component)
            if box is not None:
                top, left, bottom, right = box
                frames.append((color, box, (bottom - top + 1) * (right - left + 1)))
    frames.sort(key=lambda item: item[2])

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            for color, (top, left, bottom, right), _ in frames:
                if top < r < bottom and left < c < right:
                    output[r][c] = color
                    break
    return output
