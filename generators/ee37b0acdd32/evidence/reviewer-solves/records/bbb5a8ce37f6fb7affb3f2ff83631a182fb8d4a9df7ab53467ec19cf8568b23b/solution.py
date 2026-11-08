from collections import deque


def solve(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    colors = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = {(r, c)}
            seen.add((r, c))
            stack = [(r, c)]
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
            colors.append(color)

    owner = {
        cell: index
        for index, component in enumerate(components)
        for cell in component
    }
    graph = [set() for _ in components]
    for (r, c), first in owner.items():
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            second = owner.get((r + dr, c + dc))
            if second is not None and second != first:
                graph[first].add(second)
                graph[second].add(first)

    start = colors.index(1)
    goal = colors.index(2)
    parent = {start: None}
    queue = deque([start])
    while queue and goal not in parent:
        current = queue.popleft()
        for nxt in sorted(graph[current]):
            if nxt not in parent:
                parent[nxt] = current
                queue.append(nxt)

    path = set()
    current = goal
    while current is not None:
        path.add(current)
        current = parent[current]

    output = [[0] * w for _ in range(h)]
    for index in path:
        for r, c in components[index]:
            output[r][c] = 8
    return output
