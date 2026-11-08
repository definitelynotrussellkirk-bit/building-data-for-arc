"""Choose the smallest monochromatic component and crop its bounding rectangle."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    visited = set()
    candidates = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in visited:
                continue
            color = grid[row][col]
            pending = [(row, col)]
            visited.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        pending.append((nr, nc))
                        visited.add((nr, nc))
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            candidates.append((len(cells), top, left, bottom, right))
    _, top, left, bottom, right = min(candidates, key=lambda item: item[:3])
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
