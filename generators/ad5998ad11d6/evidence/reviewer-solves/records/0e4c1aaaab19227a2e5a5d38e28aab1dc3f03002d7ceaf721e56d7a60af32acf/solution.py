from collections import deque


def solve(grid):
    """Fill zero cells that are enclosed by 3s under 4-neighbor reachability."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])
    exterior = set()
    queue = deque()

    def add(row, col):
        if (
            0 <= row < height
            and 0 <= col < width
            and grid[row][col] == 0
            and (row, col) not in exterior
        ):
            exterior.add((row, col))
            queue.append((row, col))

    for row in range(height):
        add(row, 0)
        add(row, width - 1)
    for col in range(width):
        add(0, col)
        add(height - 1, col)

    while queue:
        row, col = queue.popleft()
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            add(row + drow, col + dcol)

    return [
        [4 if value == 0 and (row, col) not in exterior else value
         for col, value in enumerate(values)]
        for row, values in enumerate(grid)
    ]
