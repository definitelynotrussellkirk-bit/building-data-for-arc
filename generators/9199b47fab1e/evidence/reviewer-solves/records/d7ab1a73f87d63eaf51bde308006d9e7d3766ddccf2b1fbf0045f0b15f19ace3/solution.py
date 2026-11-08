from collections import deque


def solve(grid):
    """Flood cardinally from every color-2 source and paint distance bands."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [list(row) for row in grid]
    distance = {}
    queue = deque()

    for row in range(height):
        for column in range(width):
            if grid[row][column] == 2:
                distance[(row, column)] = 0
                queue.append((row, column))

    while queue:
        row, column = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, column + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if (nr, nc) in distance:
                continue
            if grid[nr][nc] not in (0, 2):
                continue
            distance[(nr, nc)] = distance[(row, column)] + 1
            queue.append((nr, nc))

    colors = (3, 4, 5)
    for (row, column), steps in distance.items():
        output[row][column] = colors[steps % 3]
    return output
