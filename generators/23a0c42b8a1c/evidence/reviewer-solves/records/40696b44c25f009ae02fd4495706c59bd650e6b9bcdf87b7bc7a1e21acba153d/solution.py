"""Infer a cropped object silhouette from the visible demonstration pairs."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    markers = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1}
    seen = set()
    touching = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color in (0, 1) or (row, column) in seen:
                continue
            cells = set()
            pending = [(row, column)]
            seen.add((row, column))
            while pending:
                r, c = pending.pop()
                cells.add((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and grid[rr][cc] == color and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        pending.append((rr, cc))
            if any((rr, cc) in markers for r, c in cells
                   for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))):
                touching.append(cells)
    if not touching:
        raise ValueError("No colored object touches the marker")
    chosen = min(touching, key=lambda cells: (len(cells), min(cells)))
    top = min(r for r, c in chosen)
    bottom = max(r for r, c in chosen)
    left = min(c for r, c in chosen)
    right = max(c for r, c in chosen)
    return [[8 if (r, c) in chosen else 0 for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]
