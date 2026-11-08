from collections import deque


def solve(grid):
    """Paint the expanded bounding box of each non-singleton red component."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }

    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbour = (row + dr, col + dc)
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)

        if len(component) == 1:
            continue
        row_min = min(row for row, _ in component)
        row_max = max(row for row, _ in component)
        col_min = min(col for _, col in component)
        col_max = max(col for _, col in component)
        for row in range(max(0, row_min - 1), min(height, row_max + 2)):
            for col in range(max(0, col_min - 1), min(width, col_max + 2)):
                if output[row][col] == 0:
                    output[row][col] = 3

    return output
