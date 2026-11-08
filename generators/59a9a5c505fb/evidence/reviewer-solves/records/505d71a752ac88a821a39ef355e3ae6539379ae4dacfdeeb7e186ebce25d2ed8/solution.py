"""Visible-example solution for the post-repair reviewer episode."""


def solve(grid):
    """Count, at each cell, how many nonzero color-component bboxes contain it."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    boxes = []

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
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            boxes.append((min(rows), min(cols), max(rows), max(cols)))

    output = [[0] * width for _ in range(height)]
    for r1, c1, r2, c2 in boxes:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                output[r][c] += 1
    return output
