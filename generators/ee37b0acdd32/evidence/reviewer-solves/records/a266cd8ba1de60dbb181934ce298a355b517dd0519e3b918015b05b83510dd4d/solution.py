from collections import deque


def solve(grid):
    """Keep the chain of monochromatic objects connecting markers 1 and 2."""
    h, w = len(grid), len(grid[0])
    owner, objects = {}, []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in owner:
                continue
            index = len(objects)
            cells = [(r, c)]
            owner[r, c] = index
            queue = deque(cells)
            while queue:
                y, x = queue.popleft()
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (0 <= yy < h and 0 <= xx < w
                            and grid[yy][xx] == grid[r][c]
                            and (yy, xx) not in owner):
                        owner[yy, xx] = index
                        cells.append((yy, xx))
                        queue.append((yy, xx))
            objects.append((grid[r][c], cells))
    edges = [set() for _ in objects]
    for (r, c), index in owner.items():
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            other = owner.get(neighbor)
            if other is not None and other != index:
                edges[index].add(other)
    start = next(i for i, (color, _) in enumerate(objects) if color == 1)
    goal = next(i for i, (color, _) in enumerate(objects) if color == 2)
    parents = {start: None}
    queue = deque([start])
    while queue and goal not in parents:
        node = queue.popleft()
        for other in sorted(edges[node]):
            if other not in parents:
                parents[other] = node
                queue.append(other)
    if goal not in parents:
        raise ValueError("Markers are not connected")
    output = [[0] * w for _ in range(h)]
    node = goal
    while node is not None:
        for r, c in objects[node][1]:
            output[r][c] = 8
        node = parents[node]
    return output
