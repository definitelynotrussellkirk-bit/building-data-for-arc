from collections import deque


def _frames(grid):
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }
    boxes = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        boxes.append((min(rows), min(cols), max(rows), max(cols)))
    return boxes


def solve(grid):
    frames = _frames(grid)
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 1:
                continue
            depth = sum(
                top < row < bottom and left < col < right
                for top, left, bottom, right in frames
            )
            output[row][col] = depth + 1 if depth else 0
    return output
