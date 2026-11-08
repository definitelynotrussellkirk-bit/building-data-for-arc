"""Crop the largest monochromatic four-connected component."""
def solve(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    best = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            component = []
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if len(component) > len(best):
                best = component
    if not best:
        return [[0]]
    top, bottom = min(r for r,c in best), max(r for r,c in best)
    left, right = min(c for r,c in best), max(c for r,c in best)
    answer = [[0] * (right-left+1) for _ in range(bottom-top+1)]
    for r, c in best:
        answer[r-top][c-left] = grid[r][c]
    return answer
