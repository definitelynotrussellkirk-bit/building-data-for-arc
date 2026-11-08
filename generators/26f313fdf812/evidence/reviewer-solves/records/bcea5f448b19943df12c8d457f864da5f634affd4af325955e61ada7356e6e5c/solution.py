from collections import deque


def solve(grid):
    """Return the pairwise size-comparison table for the colored objects.

    Non-zero cells form monochrome 4-connected objects.  Objects are ordered by
    the top-left corner of their bounding box (row, then column).  Each output
    cell compares the object for that row with the object for that column:
    1 for equal area, 2 when the row object is larger, and 3 when it is smaller.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

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
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            min_row = min(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            objects.append((min_row, min_col, len(cells)))

    objects.sort(key=lambda item: (item[0], item[1]))
    areas = [area for _, _, area in objects]

    return [
        [1 if left == right else 2 if left > right else 3 for right in areas]
        for left in areas
    ]
