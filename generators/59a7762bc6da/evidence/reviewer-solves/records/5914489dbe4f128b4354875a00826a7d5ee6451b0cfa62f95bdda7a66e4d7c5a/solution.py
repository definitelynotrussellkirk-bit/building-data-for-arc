def solve(grid):
    """Recolor eight-connected gray components whose sizes are divisible by 3."""
    result = [row[:] for row in grid]
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == 5}
    while remaining:
        start = remaining.pop()
        component = [start]
        pending = [start]
        while pending:
            r, c = pending.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    point = (r + dr, c + dc)
                    if point in remaining:
                        remaining.remove(point)
                        component.append(point)
                        pending.append(point)
        if len(component) % 3 == 0:
            for r, c in component:
                result[r][c] = 8
    return result
