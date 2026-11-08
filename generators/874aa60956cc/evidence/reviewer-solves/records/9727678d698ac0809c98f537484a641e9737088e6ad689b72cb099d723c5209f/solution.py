def solve(grid):
    points = {}
    for row_number, row in enumerate(grid):
        for column_number, color in enumerate(row):
            if color:
                points.setdefault(color, []).append((row_number, column_number))
    answer = [row[:] for row in grid]
    for color, locations in points.items():
        if len(locations) != 2:
            continue
        ys, xs = zip(*locations)
        top, bottom, left, right = min(ys), max(ys), min(xs), max(xs)
        for x in range(left, right + 1):
            answer[top][x] = color
            answer[bottom][x] = color
        for y in range(top, bottom + 1):
            answer[y][left] = color
            answer[y][right] = color
    return answer
