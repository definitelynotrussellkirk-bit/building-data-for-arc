from collections import deque


def solve(grid):
    """Spread the two endpoint colors through the cardinally connected track."""
    height, width = len(grid), len(grid[0])
    endpoints = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (2, 3):
                endpoints[value] = (r, c)
    if set(endpoints) != {2, 3}:
        raise ValueError("expected a seed of each color")

    def distances(start):
        result = {start: 0}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (0 <= nr < height and 0 <= nc < width and
                        grid[nr][nc] in (1, 2, 3) and (nr, nc) not in result):
                    result[(nr, nc)] = result[(r, c)] + 1
                    queue.append((nr, nc))
        return result

    red = distances(endpoints[2])
    green = distances(endpoints[3])
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1:
                a, b = red[(r, c)], green[(r, c)]
                output[r][c] = 2 if a < b else 3 if b < a else 4
    return output
