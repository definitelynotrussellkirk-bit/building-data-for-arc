"""Infer outward bands from the marked edges of green rectangles."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            component = []
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))

            top = min(r for r, c in component)
            bottom = max(r for r, c in component)
            left = min(c for r, c in component)
            right = max(c for r, c in component)

            for marker_r, marker_c in component:
                if grid[marker_r][marker_c] != 2:
                    continue

                if marker_r == top or marker_r == bottom:
                    radius = bottom - top
                    rows = (range(top) if marker_r == top
                            else range(bottom + 1, height))
                    for r in rows:
                        for c in range(max(0, marker_c - radius),
                                       min(width, marker_c + radius + 1)):
                            if grid[r][c] == 0:
                                result[r][c] = 2 if c == marker_c else 3
                elif marker_c == left or marker_c == right:
                    radius = right - left
                    cols = (range(left) if marker_c == left
                            else range(right + 1, width))
                    for r in range(max(0, marker_r - radius),
                                   min(height, marker_r + radius + 1)):
                        for c in cols:
                            if grid[r][c] == 0:
                                result[r][c] = 2 if r == marker_r else 3

    return result
