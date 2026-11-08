from collections import deque


def solve(grid):
    """Fill rooms by the nearest seed color along the visible door graph."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    walls = {1, 7, 9}
    owner = {}
    rooms = []

    def neighbors(r, c):
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= rr < height and 0 <= cc < width:
                yield rr, cc

    for r in range(height):
        for c in range(width):
            if grid[r][c] in walls or (r, c) in owner:
                continue
            index = len(rooms)
            cells = [(r, c)]
            owner[r, c] = index
            queue = deque(cells)
            while queue:
                rr, cc = queue.popleft()
                for pos in neighbors(rr, cc):
                    if pos not in owner and grid[pos[0]][pos[1]] not in walls:
                        owner[pos] = index
                        cells.append(pos)
                        queue.append(pos)
            rooms.append(cells)

    graph = [set() for _ in rooms]
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 7:
                incident = {owner[pos] for pos in neighbors(r, c) if pos in owner}
                for index in incident:
                    graph[index].update(incident - {index})

    seeds = []
    for index, cells in enumerate(rooms):
        colors = [grid[r][c] for r, c in cells if grid[r][c] != 0]
        if colors:
            seeds.append((index, min(colors)))
    if not seeds:
        raise ValueError("No colored seed room")

    distances = []
    for source, color in seeds:
        dist = [float("inf")] * len(rooms)
        dist[source] = 0
        queue = deque([source])
        while queue:
            here = queue.popleft()
            for there in graph[here]:
                if dist[there] == float("inf"):
                    dist[there] = dist[here] + 1
                    queue.append(there)
        distances.append((color, dist))

    result = [row[:] for row in grid]
    for index, cells in enumerate(rooms):
        best = min(dist[index] for _, dist in distances)
        nearest_colors = {color for color, dist in distances if dist[index] == best}
        fill = next(iter(nearest_colors)) if len(nearest_colors) == 1 else 8
        for r, c in cells:
            result[r][c] = fill
    return result
