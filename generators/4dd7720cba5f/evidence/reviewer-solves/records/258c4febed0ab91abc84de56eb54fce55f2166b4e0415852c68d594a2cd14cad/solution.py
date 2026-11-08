"""Union interior marks among rectangular frames of the same color."""


def solve(grid):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    visited = set()
    frames = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            stack = [(row, col)]
            visited.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited
                            and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            if bottom - top < 2 or right - left < 2:
                continue
            if not (all(grid[top][c] == grid[bottom][c] == color
                        for c in range(left, right + 1))
                    and all(grid[r][left] == grid[r][right] == color
                            for r in range(top, bottom + 1))):
                continue
            frames.append((top, left, bottom, right, color))
    masks = {}
    for top, left, bottom, right, color in frames:
        key = (color, bottom - top, right - left)
        mask = masks.setdefault(key, set())
        mask.update((r - top, c - left)
                    for r in range(top + 1, bottom)
                    for c in range(left + 1, right)
                    if grid[r][c] == color)
    for top, left, bottom, right, color in frames:
        for dr, dc in masks[(color, bottom - top, right - left)]:
            out[top + dr][left + dc] = color
    return out
