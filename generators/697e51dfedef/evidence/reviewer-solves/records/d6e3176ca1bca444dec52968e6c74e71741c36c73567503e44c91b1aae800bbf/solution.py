def solve(grid):
    """Recolor the three objects by increasing cell count: 2, 4, 8."""
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc),
                               (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            objects.append(cells)
    if len(objects) != 3 or len({len(cells) for cells in objects}) != 3:
        raise ValueError("Expected three objects of distinct sizes")
    output = [list(row) for row in grid]
    for color, cells in zip((2, 4, 8), sorted(objects, key=len)):
        for r, c in cells:
            output[r][c] = color
    return output
