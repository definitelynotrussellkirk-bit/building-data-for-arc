def solve(grid):
    """Place the largest 3-shape at markers 1 and 2; show its overlap as 8."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0] * width for _ in range(height)]
    markers = {}
    remaining = set()
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 3:
                remaining.add((r, c))
            elif color in (1, 2):
                markers[color] = (r, c)

    largest = set()
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        pending = [start]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        if len(component) > len(largest):
            largest = component

    if not largest or 1 not in markers or 2 not in markers:
        return result
    top = min(r for r, _ in largest)
    left = min(c for _, c in largest)
    shape = {(r - top, c - left) for r, c in largest}
    first_r, first_c = markers[1]
    second_r, second_c = markers[2]
    first = {(r + first_r, c + first_c) for r, c in shape}
    second = {(r + second_r, c + second_c) for r, c in shape}
    for r, c in first & second:
        if 0 <= r < height and 0 <= c < width:
            result[r][c] = 8
    return result
