"""Post-repair attempt based on the displayed examples; prior exposure declared."""

def solve(grid):
    cells = {1: [], 2: []}
    key = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in cells:
                cells[value].append((r, c))
            elif value != 0 and key is None:
                key = value
    if not cells[1] or not cells[2] or key is None:
        raise ValueError("Expected two colored shapes and a separate color key")
    boxes = []
    for color in (1, 2):
        points = cells[color]
        boxes.append((min(r for r, c in points), min(c for r, c in points),
                      max(r for r, c in points), max(c for r, c in points)))
    top = max(box[0] for box in boxes)
    left = max(box[1] for box in boxes)
    bottom = min(box[2] for box in boxes)
    right = min(box[3] for box in boxes)
    output = [[0] * len(row) for row in grid]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            output[r][c] = key
    return output
