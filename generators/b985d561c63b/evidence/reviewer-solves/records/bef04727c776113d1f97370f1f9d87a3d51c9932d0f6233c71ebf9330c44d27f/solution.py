def solve(grid):
    h, w = len(grid), len(grid[0])
    source_cells = [(r, c) for r in range(h) for c in range(w)
                    if grid[r][c] != 0 and grid[r][c] != 5]
    if not source_cells:
        raise ValueError("Expected one colored source")
    top = min(r for r, c in source_cells)
    left = min(c for r, c in source_cells)
    bottom = max(r for r, c in source_cells) + 1
    right = max(c for r, c in source_cells) + 1
    pattern = [row[left:right] for row in grid[top:bottom]]
    seen = set()
    anchors = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            component, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                a, b = stack.pop()
                component.append((a, b))
                for u, v in ((a-1, b), (a+1, b), (a, b-1), (a, b+1)):
                    if (0 <= u < h and 0 <= v < w and grid[u][v] == 5
                            and (u, v) not in seen):
                        seen.add((u, v))
                        stack.append((u, v))
            anchors.append((min(a for a, b in component), min(b for a, b in component)))
    out = [list(row) for row in grid]
    for r, c in anchors:
        for dr, row in enumerate(pattern):
            for dc, value in enumerate(row):
                out[r+dr][c+dc] = value
    return out
