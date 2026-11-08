"""Visible-example solution: crop the main object and apply external color keys."""
def solve(grid):
    height, width = len(grid), len(grid[0])
    visited = set()
    components = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in visited:
                continue
            color = grid[r][c]
            cells = []
            pending = [(r, c)]
            visited.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in visited and grid[nr][nc] == color:
                        visited.add((nr, nc))
                        pending.append((nr, nc))
            components.append(cells)
    if not components:
        return [row[:] for row in grid]
    main = max(components, key=len)
    top, bottom = min(r for r, _ in main), max(r for r, _ in main)
    left, right = min(c for _, c in main), max(c for _, c in main)
    def outside(r, c):
        return not (top <= r <= bottom and left <= c <= right)
    replacements = {}
    for r in range(height):
        for c in range(width - 1):
            if outside(r, c) and outside(r, c + 1) and grid[r][c] and grid[r][c+1]:
                replacements[grid[r][c+1]] = grid[r][c]
    return [[replacements.get(grid[r][c], grid[r][c]) for c in range(left, right+1)]
            for r in range(top, bottom+1)]
