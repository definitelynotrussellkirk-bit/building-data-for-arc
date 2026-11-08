"""Solution inferred from the displayed pairs, without reference imports."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    outside = set()
    frontier = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 and (row in (0, height - 1) or col in (0, width - 1)):
                outside.add((row, col))
                frontier.append((row, col))
    while frontier:
        row, col = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (row + dr, col + dc)
            nr, nc = point
            if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == 0 and point not in outside:
                outside.add(point)
                frontier.append(point)
    return [
        [cell if cell else (3 if (row, col) in outside else 2)
         for col, cell in enumerate(cells)]
        for row, cells in enumerate(grid)
    ]
