def solve(grid):
    """Crop objects, rotate tall crops clockwise, sort by perimeter, stack."""
    height, width = len(grid), len(grid[0])
    seen = set()
    items = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            r0 = min(r for r, _ in cells)
            r1 = max(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            c1 = max(c for _, c in cells)
            crop = [values[c0:c1 + 1] for values in grid[r0:r1 + 1]]
            if len(crop) > len(crop[0]):
                crop = [list(values) for values in zip(*crop[::-1])]
            perimeter = 2 * ((r1 - r0 + 1) + (c1 - c0 + 1))
            items.append((perimeter, r0, c0, crop))

    items.sort(key=lambda item: (-item[0], item[1], item[2]))
    shapes = [item[3] for item in items]
    out_height = sum(len(shape) for shape in shapes) + max(0, len(shapes) - 1)
    out_width = max(len(shape[0]) for shape in shapes)
    output = [[0 for _ in range(out_width)] for _ in range(out_height)]
    top = 0
    for shape in shapes:
        for r, values in enumerate(shape):
            for c, value in enumerate(values):
                if value != 0:
                    output[top + r][c] = value
        top += len(shape) + 1
    return output
