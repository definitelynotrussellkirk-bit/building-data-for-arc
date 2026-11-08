from collections import deque


def solve(grid):
    """Color every open cell on a shortest four-neighbor red-to-green path."""
    h, w = len(grid), len(grid[0])
    start = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 2)
    target = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 3)

    def distances(origin):
        distance = {origin: 0}
        queue = deque([origin])
        while queue:
            r, c = queue.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 5
                        and (rr, cc) not in distance):
                    distance[rr, cc] = distance[r, c] + 1
                    queue.append((rr, cc))
        return distance

    from_start, from_target = distances(start), distances(target)
    output = [list(row) for row in grid]
    if target not in from_start:
        return output
    shortest = from_start[target]
    for (r, c), steps in from_start.items():
        if grid[r][c] == 0 and steps + from_target.get((r, c), float("inf")) == shortest:
            output[r][c] = 8
    return output
