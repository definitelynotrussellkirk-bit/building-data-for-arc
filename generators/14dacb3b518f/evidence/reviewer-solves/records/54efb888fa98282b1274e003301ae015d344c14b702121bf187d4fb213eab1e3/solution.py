from collections import deque


def _has_hole(cells):
    """Return True when this 4-connected object encloses background in its box."""
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    height = r1 - r0 + 1
    width = c1 - c0 + 1

    occupied = {(r - r0, c - c0) for r, c in cells}
    outside = set()
    queue = deque()

    def add_if_background(r, c):
        point = (r, c)
        if point not in occupied and point not in outside:
            outside.add(point)
            queue.append(point)

    for r in range(height):
        add_if_background(r, 0)
        add_if_background(r, width - 1)
    for c in range(width):
        add_if_background(0, c)
        add_if_background(height - 1, c)

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width:
                add_if_background(nr, nc)

    return any(
        (r, c) not in occupied and (r, c) not in outside
        for r in range(height)
        for c in range(width)
    )


def solve(grid):
    """Color each nonzero object 8 if it encloses a hole, otherwise 2."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue

            component = set()
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            while queue:
                r, c = queue.popleft()
                component.add((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            color = 8 if _has_hole(component) else 2
            for r, c in component:
                result[r][c] = color

    return result
