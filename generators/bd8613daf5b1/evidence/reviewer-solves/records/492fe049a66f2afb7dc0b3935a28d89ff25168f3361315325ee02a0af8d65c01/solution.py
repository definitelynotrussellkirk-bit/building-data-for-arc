from collections import deque


def solve(grid):
    """Crop the foreground and label it by orthogonal depth from background."""
    occupied = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return []

    top = min(r for r, _ in occupied)
    bottom = max(r for r, _ in occupied)
    left = min(c for _, c in occupied)
    right = max(c for _, c in occupied)
    height = bottom - top + 1
    width = right - left + 1

    # The zero frame represents the background outside the tight crop.
    mask = [[0] * (width + 2)]
    for r in range(top, bottom + 1):
        mask.append(
            [0] + [int(grid[r][c] != 0) for c in range(left, right + 1)] + [0]
        )
    mask.append([0] * (width + 2))

    distances = [[None] * (width + 2) for _ in range(height + 2)]
    queue = deque()
    for r in range(height + 2):
        for c in range(width + 2):
            if mask[r][c] == 0:
                distances[r][c] = 0
                queue.append((r, c))

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < height + 2
                and 0 <= nc < width + 2
                and distances[nr][nc] is None
            ):
                distances[nr][nc] = distances[r][c] + 1
                queue.append((nr, nc))

    return [row[1:-1] for row in distances[1:-1]]
