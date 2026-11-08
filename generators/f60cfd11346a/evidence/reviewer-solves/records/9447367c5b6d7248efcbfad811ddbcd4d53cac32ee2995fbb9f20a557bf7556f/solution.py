from collections import deque


def solve(grid):
    """Color the zero-valued region connected orthogonally to the blue seed 2."""
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    seeds = [
        (r, c)
        for r, row in enumerate(out)
        for c, value in enumerate(row)
        if value == 2
    ]
    queue = deque(seeds)
    seen = set(seeds)

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if (nr, nc) in seen or out[nr][nc] != 0:
                continue
            seen.add((nr, nc))
            out[nr][nc] = 8
            queue.append((nr, nc))

    return out
