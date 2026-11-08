from collections import deque


def solve(grid):
    """Recolor each 4-connected yellow component by whether it encloses a hole."""
    height = len(grid)
    width = len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 4}
    out = [row[:] for row in grid]
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)

        min_r = min(r for r, _ in component)
        max_r = max(r for r, _ in component)
        min_c = min(c for _, c in component)
        max_c = max(c for _, c in component)

        # Flood the component's bounding-box background from its boundary.
        empty = {
            (r, c)
            for r in range(min_r, max_r + 1)
            for c in range(min_c, max_c + 1)
            if (r, c) not in component
        }
        exterior = {
            point
            for point in empty
            if point[0] in (min_r, max_r) or point[1] in (min_c, max_c)
        }
        queue = deque(exterior)
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                point = (r + dr, c + dc)
                if point in empty and point not in exterior:
                    exterior.add(point)
                    queue.append(point)

        has_hole = bool(empty - exterior)
        new_color = 8 if has_hole else 2
        for r, c in component:
            out[r][c] = new_color

    return out
