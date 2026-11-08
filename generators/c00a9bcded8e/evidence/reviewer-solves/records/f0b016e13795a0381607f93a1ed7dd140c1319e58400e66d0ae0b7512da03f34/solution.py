def solve(grid):
    """Compress the solid colored rectangles into their spatial row layout."""
    height, width = len(grid), len(grid[0])
    seen = set()
    rectangles = []
    for y in range(height):
        for x in range(width):
            if (y, x) in seen:
                continue
            color = grid[y][x]
            seen.add((y, x))
            pending = [(y, x)]
            cells = []
            while pending:
                cy, cx = pending.pop()
                cells.append((cy, cx))
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < height and 0 <= nx < width and (ny, nx) not in seen and grid[ny][nx] == color:
                        seen.add((ny, nx))
                        pending.append((ny, nx))
            top = min(cy for cy, _ in cells)
            bottom = max(cy for cy, _ in cells)
            left = min(cx for _, cx in cells)
            right = max(cx for _, cx in cells)
            if color and bottom - top + 1 >= 3 and right - left + 1 >= 3 and len(cells) == (bottom - top + 1) * (right - left + 1):
                rectangles.append((top, bottom, left, color))
    rows = []
    for rect in sorted(rectangles):
        if not rows or rect[0] > max(item[1] for item in rows[-1]):
            rows.append([rect])
        else:
            rows[-1].append(rect)
    return [[item[3] for item in sorted(row, key=lambda item: item[2])] for row in rows]
