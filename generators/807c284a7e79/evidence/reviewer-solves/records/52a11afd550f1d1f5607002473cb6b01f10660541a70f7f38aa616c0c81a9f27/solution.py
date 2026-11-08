from collections import deque


def solve(grid):
    """Alternate colors 3 and 4 through the open region of the red seed."""
    result = [list(row) for row in grid]
    if not result or not result[0]:
        return result
    height, width = len(result), len(result[0])
    seed = next(
        ((r, c) for r in range(height) for c in range(width) if grid[r][c] == 2),
        None,
    )
    if seed is None:
        return result

    queue = deque([(seed[0], seed[1], 0)])
    seen = {seed}
    while queue:
        r, c, distance = queue.popleft()
        result[r][c] = 3 if distance % 2 == 0 else 4
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] in (0, 2)
                and (nr, nc) not in seen
            ):
                seen.add((nr, nc))
                queue.append((nr, nc, distance + 1))
    return result
