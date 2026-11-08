from collections import deque


def solve(grid):
    """Recolor every nonzero component orthogonally attached to color 1."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    seeds = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1:
                continue
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    color = grid[nr][nc]
                    if color not in (0, 1):
                        seeds.add((nr, nc))

    visited = set()
    for seed in seeds:
        if seed in visited:
            continue
        color = grid[seed[0]][seed[1]]
        queue = deque([seed])
        visited.add(seed)
        component = []

        while queue:
            row, col = queue.popleft()
            component.append((row, col))
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if not (0 <= nr < height and 0 <= nc < width):
                    continue
                if (nr, nc) in visited or grid[nr][nc] != color:
                    continue
                visited.add((nr, nc))
                queue.append((nr, nc))

        for row, col in component:
            out[row][col] = 4

    return out
