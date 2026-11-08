from collections import deque


def solve(grid):
    """Connect 1→2→3→4 by shortest orthogonal routes avoiding gray walls."""
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    markers = {grid[r][c]: (r, c) for r in range(height)
               for c in range(width) if grid[r][c] in (1, 2, 3, 4)}
    for label in (1, 2, 3):
        start, goal = markers[label], markers[label + 1]
        parent = {start: None}
        queue = deque([start])
        while queue and goal not in parent:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                nr, nc = point
                if (0 <= nr < height and 0 <= nc < width
                        and grid[nr][nc] != 5 and point not in parent):
                    parent[point] = (r, c)
                    queue.append(point)
        if goal not in parent:
            raise ValueError("Consecutive numbered markers are disconnected")
        point = goal
        while point is not None:
            r, c = point
            if grid[r][c] == 0:
                output[r][c] = 8
            point = parent[point]
    return output
