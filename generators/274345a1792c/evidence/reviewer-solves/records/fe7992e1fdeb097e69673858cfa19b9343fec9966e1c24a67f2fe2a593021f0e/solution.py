def solve(grid):
    """Stamp the visible color-9 silhouette at every controlled color-6 anchor."""
    rows, cols = len(grid), len(grid[0])
    cells = [(r, c) for r, row in enumerate(grid)
             for c, color in enumerate(row) if color == 9]
    if not cells:
        raise ValueError("No prototype is visible")
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    mask = [[grid[r][c] == 9 for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]

    def clockwise(shape):
        return [list(row) for row in zip(*shape[::-1])]

    reflected = [row[::-1] for row in mask]
    transforms = {1: mask, 2: clockwise(mask),
                  3: reflected, 4: clockwise(reflected)}
    output = [list(row) for row in grid]
    anchors = [(r, c, grid[r - 1][c]) for r in range(1, rows)
               for c in range(cols)
               if grid[r][c] == 6 and grid[r - 1][c] in transforms]
    for anchor_r, anchor_c, code in anchors:
        for dr, row in enumerate(transforms[code]):
            for dc, occupied in enumerate(row):
                r, c = anchor_r + dr, anchor_c + dc
                if occupied and 0 <= r < rows and 0 <= c < cols:
                    output[r][c] = 8
    return output
