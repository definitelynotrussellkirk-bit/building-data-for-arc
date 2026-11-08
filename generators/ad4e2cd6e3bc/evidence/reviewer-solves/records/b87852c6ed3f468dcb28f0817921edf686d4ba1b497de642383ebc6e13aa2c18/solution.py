from collections import deque


def solve(grid):
    """Color the 4-connected zero region touching the red marker azure."""
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    queue = deque()
    seen = set()
    for row in range(height):
        for col in range(width):
            if out[row][col] == 2:
                queue.append((row, col))
                seen.add((row, col))

    while queue:
        row, col = queue.popleft()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            next_row = row + drow
            next_col = col + dcol
            if not (0 <= next_row < height and 0 <= next_col < width):
                continue
            if (next_row, next_col) in seen:
                continue
            if out[next_row][next_col] != 0:
                continue
            seen.add((next_row, next_col))
            out[next_row][next_col] = 8
            queue.append((next_row, next_col))

    return out
