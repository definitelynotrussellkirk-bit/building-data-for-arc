from collections import deque


def solve(grid):
    """Connect checkpoints 2->3->4->7 by deterministic shortest paths."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    checkpoints = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (2, 3, 4, 7):
                checkpoints[value] = (row, col)

    def shortest_path(start, goal):
        queue = deque([start])
        parent = {start: None}
        # The visible examples resolve symmetric shortest paths in this order.
        for_pop = ((-1, 0), (1, 0), (0, -1), (0, 1))
        while queue:
            point = queue.popleft()
            if point == goal:
                break
            for dr, dc in for_pop:
                nxt = (point[0] + dr, point[1] + dc)
                if (
                    0 <= nxt[0] < height
                    and 0 <= nxt[1] < width
                    and grid[nxt[0]][nxt[1]] != 5
                    and nxt not in parent
                ):
                    parent[nxt] = point
                    queue.append(nxt)
        if goal not in parent:
            return []
        answer = []
        point = goal
        while point is not None:
            answer.append(point)
            point = parent[point]
        answer.reverse()
        return answer

    route = set()
    for first, second in ((2, 3), (3, 4), (4, 7)):
        path = shortest_path(checkpoints[first], checkpoints[second])
        route.update(path[1:-1])

    output = [list(row) for row in grid]
    for row, col in route:
        output[row][col] = 8
    return output
