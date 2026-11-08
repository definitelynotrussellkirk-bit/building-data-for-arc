"""Visible-example solution for the reviewer solve episode."""

CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def solve(grid):
    if not grid or not grid[0]:
        return [[0]]

    height = len(grid)
    width = len(grid[0])
    foreground = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 0
    }
    if not foreground:
        return [[0]]

    # Discover binary 4-connected components, deliberately ignoring color.
    unseen = set(foreground)
    components = []
    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        todo = [start]
        component = {start}
        while todo:
            r, c = todo.pop()
            for dr, dc in CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        components.append(component)

    depths = [[0 for _ in range(width)] for _ in range(height)]
    for component in components:
        remaining = set(component)
        layer = 1
        while remaining:
            boundary = {
                (r, c)
                for r, c in remaining
                if any((r + dr, c + dc) not in remaining for dr, dc in CARDINAL)
            }
            for r, c in boundary:
                depths[r][c] = layer
            remaining.difference_update(boundary)
            layer += 1

    min_r = min(r for r, _ in foreground)
    max_r = max(r for r, _ in foreground)
    min_c = min(c for _, c in foreground)
    max_c = max(c for _, c in foreground)
    return [row[min_c : max_c + 1] for row in depths[min_r : max_r + 1]]
