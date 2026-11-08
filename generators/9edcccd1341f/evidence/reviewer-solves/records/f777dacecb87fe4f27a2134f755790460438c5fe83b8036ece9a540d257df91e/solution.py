from collections import Counter


def solve(grid):
    """Preserve the top key, recolor the frame, and box the dominant payload."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    frame_color = grid[1][0]

    payload = [
        (r, c, grid[r][c])
        for r in range(2, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] not in (0, frame_color)
    ]
    counts = Counter(value for _, _, value in payload)
    if not counts:
        return [row[:] for row in grid]
    winner = max(counts, key=counts.get)
    cells = [(r, c) for r, c, value in payload if value == winner]
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)

    out = [[0] * w for _ in range(h)]
    out[0] = list(grid[0])

    for c in range(w):
        out[1][c] = winner
        out[h - 1][c] = winner
    for r in range(2, h - 1):
        out[r][0] = winner
        out[r][w - 1] = winner

    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if r in (r1, r2) or c in (c1, c2):
                out[r][c] = winner
    return out
