from collections.abc import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Project the red rectangle to the grid edges, except along vetoed rays."""
    source = [list(row) for row in grid]
    if not source or not source[0]:
        return source

    height = len(source)
    width = len(source[0])
    red_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] == 2
    ]
    if not red_cells:
        return source

    top = min(row for row, _ in red_cells)
    bottom = max(row for row, _ in red_cells)
    left = min(col for _, col in red_cells)
    right = max(col for _, col in red_cells)

    result = [row[:] for row in source]

    def is_marker(value: int) -> bool:
        return value not in (0, 2)

    for row in range(top, bottom + 1):
        if not any(is_marker(source[row][col]) for col in range(left)):
            for col in range(left):
                result[row][col] = 2
        if not any(is_marker(source[row][col]) for col in range(right + 1, width)):
            for col in range(right + 1, width):
                result[row][col] = 2

    for col in range(left, right + 1):
        if not any(is_marker(source[row][col]) for row in range(top)):
            for row in range(top):
                result[row][col] = 2
        if not any(is_marker(source[row][col]) for row in range(bottom + 1, height)):
            for row in range(bottom + 1, height):
                result[row][col] = 2

    return result
