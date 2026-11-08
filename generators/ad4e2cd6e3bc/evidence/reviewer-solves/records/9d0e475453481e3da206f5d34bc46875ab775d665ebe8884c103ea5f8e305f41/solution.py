"""Fill the zero-valued region reached orthogonally from red markers."""

from collections import deque


def solve(grid):
    result = [list(row) for row in grid]
    if not result or not result[0]:
        return result

    height, width = len(result), len(result[0])
    pending = deque(
        (row, col)
        for row in range(height)
        for col in range(width)
        if result[row][col] == 2
    )

    while pending:
        row, col = pending.popleft()
        for next_row, next_col in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if (
                0 <= next_row < height
                and 0 <= next_col < width
                and result[next_row][next_col] == 0
            ):
                result[next_row][next_col] = 8
                pending.append((next_row, next_col))

    return result
