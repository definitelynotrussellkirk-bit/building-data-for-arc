"""Visible-example solution: extend marked rectangles toward the grid edge."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    seen = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            marks = [(r, c) for r, c in cells if grid[r][c] == 2]
            if len(marks) != 1:
                continue
            mr, mc = marks[0]
            top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
            left, right = min(c for _, c in cells), max(c for _, c in cells)
            if mr == top or mr == bottom:
                dr = -1 if mr == top else 1
                radius = bottom - top
                r = mr + dr
                while 0 <= r < height:
                    for c in range(max(0, mc-radius), min(width, mc+radius+1)):
                        result[r][c] = 2 if c == mc else 3
                    r += dr
            else:
                dc = -1 if mc == left else 1
                radius = right - left
                c = mc + dc
                while 0 <= c < width:
                    for r in range(max(0, mr-radius), min(height, mr+radius+1)):
                        result[r][c] = 2 if r == mr else 3
                    c += dc
    return result
