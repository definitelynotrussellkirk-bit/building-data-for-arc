"""Solver inferred from the public examples in this solve episode."""


def solve(grid):
    if not grid or not grid[0]:
        raise ValueError("expected a nonempty grid")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    background = grid[0][0]
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    boxes = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = [start]
        while stack:
            row, col = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    neighbor = (row + dr, col + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.append(neighbor)
                        stack.append(neighbor)
        boxes.append((
            min(row for row, _ in component),
            min(col for _, col in component),
            max(row for row, _ in component),
            max(col for _, col in component),
        ))
    if not boxes:
        raise ValueError("no panels found")
    boxes.sort()
    out_height = boxes[0][2] - boxes[0][0] + 1
    out_width = boxes[0][3] - boxes[0][1] + 1
    if any(bottom - top + 1 != out_height or right - left + 1 != out_width
           for top, left, bottom, right in boxes):
        raise ValueError("panels must have equal dimensions")
    answer = [[0] * out_width for _ in range(out_height)]
    for top, left, _, _ in boxes:
        for row in range(out_height):
            for col in range(out_width):
                value = grid[top + row][left + col]
                if answer[row][col] == 0 and value not in (0, background):
                    answer[row][col] = value
    return answer
