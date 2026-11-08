from collections import Counter

def solve(grid):
    if not grid or not grid[0]:
        raise ValueError("Expected a nonempty grid")
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("Expected rectangular input")
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    output = [[background] * w for _ in range(h)]
    visited = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == background or (r, c) in visited:
                continue
            stack = [(r, c)]
            visited.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in visited and grid[nr][nc] == color:
                        visited.add((nr,nc))
                        stack.append((nr,nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            cr = (min(rows) + max(rows)) // 2
            cc = (min(cols) + max(cols)) // 2
            if len(set(rows)) != 1 and len(set(cols)) != 1:
                raise ValueError("Visible rule only supports straight components")
            for rr, col in cells:
                nr, nc = cr + col - cc, cc - rr + cr
                if 0 <= nr < h and 0 <= nc < w:
                    output[nr][nc] = color
    return output
