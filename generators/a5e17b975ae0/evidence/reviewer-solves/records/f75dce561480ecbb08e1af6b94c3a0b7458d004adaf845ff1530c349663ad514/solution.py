from collections import deque


def solve(grid):
    """Flood each colored key through its original 4-connected chamber."""
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    height = len(original)
    width = len(original[0]) if height else 0

    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] not in (0, 5, 9)
    ]
    for start_row, start_col in seeds:
        color = original[start_row][start_col]
        queue = deque([(start_row, start_col)])
        seen = {(start_row, start_col)}
        while queue:
            row, col = queue.popleft()
            output[row][col] = color
            for next_row, next_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                if (next_row, next_col) in seen:
                    continue
                value = original[next_row][next_col]
                if value in (5, 9) or value not in (0, color):
                    continue
                seen.add((next_row, next_col))
                queue.append((next_row, next_col))
    return output
