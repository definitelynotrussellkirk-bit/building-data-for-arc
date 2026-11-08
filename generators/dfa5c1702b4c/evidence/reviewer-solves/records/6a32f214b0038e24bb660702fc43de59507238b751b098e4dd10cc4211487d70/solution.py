"""Fresh visible-example solve using connected components and interval overlap."""

def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    boxes = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            rs, cs = zip(*cells)
            boxes.append((min(rs), min(cs), max(rs), max(cs)))
    boxes.sort(key=lambda b: (b[0], b[1]))
    answer = []
    for a in boxes:
        answer.append([
            int(max(a[0], b[0]) <= min(a[2], b[2]))
            + 2 * int(max(a[1], b[1]) <= min(a[3], b[3]))
            for b in boxes
        ])
    return answer
