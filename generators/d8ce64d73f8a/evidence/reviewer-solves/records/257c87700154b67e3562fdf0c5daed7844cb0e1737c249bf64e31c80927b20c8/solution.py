from collections import deque


def solve(grid):
    """Flood-fill the non-gray chamber containing the unique red marker."""
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    starts = [
        (r, c)
        for r, row in enumerate(out)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(starts) != 1:
        raise ValueError(f"expected exactly one red marker, found {len(starts)}")

    queue = deque(starts)
    seen = set(starts)
    while queue:
        r, c = queue.popleft()
        out[r][c] = 8
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in seen
                and out[nr][nc] != 5
            ):
                seen.add((nr, nc))
                queue.append((nr, nc))

    return out
