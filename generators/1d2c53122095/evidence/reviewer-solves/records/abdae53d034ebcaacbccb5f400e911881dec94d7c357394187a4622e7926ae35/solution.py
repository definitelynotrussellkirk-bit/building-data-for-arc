from collections import deque


def _yellow_frame_boxes(grid):
    """Return color-4 connected-component bounding boxes, largest first."""
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 4
    }
    boxes = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        boxes.append((min(rows), min(cols), max(rows), max(cols)))

    boxes.sort(
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )
    return boxes


def solve(grid):
    """Fill the nested yellow band selected by the top-row red count."""
    output = [row[:] for row in grid]
    depth = sum(value == 2 for value in grid[0])
    frames = _yellow_frame_boxes(grid)

    target = frames[depth - 1]
    inner = frames[depth] if depth < len(frames) else None
    top, left, bottom, right = target

    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            if output[row][col] != 0:
                continue
            if inner is not None:
                inner_top, inner_left, inner_bottom, inner_right = inner
                if inner_top < row < inner_bottom and inner_left < col < inner_right:
                    continue
            output[row][col] = 8
    return output
