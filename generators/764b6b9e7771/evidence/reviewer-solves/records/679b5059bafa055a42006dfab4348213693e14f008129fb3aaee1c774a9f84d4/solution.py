"""Connect the visible directed start through unvisited turning points to a wall."""


def solve(grid):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            positions.setdefault(value, []).append((r, c))
    tail = positions[2][0]
    head = positions[1][0]
    dr, dc = head[0] - tail[0], head[1] - tail[1]
    dr = (dr > 0) - (dr < 0)
    dc = (dc > 0) - (dc < 0)
    current = head
    visited = {tail, head}

    def ray(origin, direction):
        r, c = origin
        dy, dx = direction
        r, c = r + dy, c + dx
        while 0 <= r < height and 0 <= c < width:
            if grid[r][c] != 0:
                if (r, c) in visited:
                    return None
                if grid[r][c] in (4, 5, 6):
                    return (r, c)
                return None
            r, c = r + dy, c + dx
        return None

    direction = (dr, dc)
    for _ in range(height * width):
        target = ray(current, direction)
        if target is None:
            raise ValueError("No next visible point along the directed path")
        r, c = current
        while (r, c) != target:
            r, c = r + direction[0], c + direction[1]
            if out[r][c] == 0:
                out[r][c] = 8
        visited.add(target)
        current = target
        if grid[r][c] == 5:
            return out
        options = []
        for turn in ((-direction[1], direction[0]), (direction[1], -direction[0])):
            if ray(current, turn) is not None:
                options.append(turn)
        if len(options) != 1:
            raise ValueError("The visible turning rule is ambiguous or incomplete")
        direction = options[0]
    raise ValueError("Path did not reach the wall")
