from copy import deepcopy

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(cells):
    unseen = set(cells)
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def solve(grid):
    """Recolor each body component by successive cardinal boundary layers."""
    out = deepcopy(grid)
    if not grid or not grid[0]:
        return out

    palette = [value for value in grid[0] if value != 0]
    if not palette:
        return out

    body = {
        (r, c)
        for r in range(1, len(grid))
        for c, value in enumerate(grid[r])
        if value != 0
    }
    for component in _components(body):
        remaining = set(component)
        layer = 0
        while remaining:
            boundary = {
                (r, c)
                for r, c in remaining
                if any((r + dr, c + dc) not in remaining for dr, dc in _CARDINAL)
            }
            color = palette[min(layer, len(palette) - 1)]
            for r, c in boundary:
                out[r][c] = color
            remaining.difference_update(boundary)
            layer += 1
    return out
