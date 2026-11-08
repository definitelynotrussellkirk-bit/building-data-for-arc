from collections import Counter, deque


def solve(grid):
    """Fill zero-valued regions enclosed by outlines with the repeated corner color."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    out = [list(row) for row in grid]

    corners = (
        grid[0][0],
        grid[0][width - 1],
        grid[height - 1][0],
        grid[height - 1][width - 1],
    )
    marker_counts = Counter(color for color in corners if color not in (0, 3))
    if not marker_counts:
        return out
    fill_color = marker_counts.most_common(1)[0][0]

    exterior = [[False] * width for _ in range(height)]
    queue = deque()

    def seed(row, col):
        if out[row][col] == 0 and not exterior[row][col]:
            exterior[row][col] = True
            queue.append((row, col))

    for col in range(width):
        seed(0, col)
        seed(height - 1, col)
    for row in range(height):
        seed(row, 0)
        seed(row, width - 1)

    while queue:
        row, col = queue.popleft()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            new_row = row + drow
            new_col = col + dcol
            if (
                0 <= new_row < height
                and 0 <= new_col < width
                and out[new_row][new_col] == 0
                and not exterior[new_row][new_col]
            ):
                exterior[new_row][new_col] = True
                queue.append((new_row, new_col))

    for row in range(height):
        for col in range(width):
            if out[row][col] == 0 and not exterior[row][col]:
                out[row][col] = fill_color

    return out
