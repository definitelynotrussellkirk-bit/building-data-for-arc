"""Infer an object's recoloring from its number of enclosed regions."""


def _components(cells):
    remaining = set(cells)
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = [start]
        for row, col in component:
            for neighbor in ((row - 1, col), (row + 1, col),
                             (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.append(neighbor)
        yield component


def solve(grid):
    output = [list(row) for row in grid]
    objects = _components((r, c) for r, row in enumerate(grid)
                          for c, value in enumerate(row) if value == 8)
    for cells in objects:
        r0 = min(r for r, c in cells) - 1
        r1 = max(r for r, c in cells) + 1
        c0 = min(c for r, c in cells) - 1
        c1 = max(c for r, c in cells) + 1
        complement = {(r, c) for r in range(r0, r1 + 1)
                      for c in range(c0, c1 + 1)} - set(cells)
        holes = sum(not any(r in (r0, r1) or c in (c0, c1)
                            for r, c in region)
                    for region in _components(complement))
        color = {1: 1, 2: 2, 3: 3, 4: 7}.get(holes, 8)
        for r, c in cells:
            output[r][c] = color
    return output
