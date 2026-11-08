"""Final-source visible-example solve; earlier rule exposure is declared."""
from collections import Counter

def solve(grid):
    h, w = len(grid), len(grid[0])
    frequency = Counter(c for row in grid for c in row if c != 0)
    visited = set()
    winner = None
    rank = None
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r,c) in visited:
                continue
            stack = [(r,c)]
            visited.add((r,c))
            cells = []
            while stack:
                y,x = stack.pop()
                cells.append((y,x))
                for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0 <= yy < h and 0 <= xx < w and (yy,xx) not in visited and grid[yy][xx] == color:
                        visited.add((yy,xx))
                        stack.append((yy,xx))
            if rank is None or frequency[color] < rank:
                rank, winner = frequency[color], cells
    if winner is None:
        raise ValueError("No foreground component")
    r0,r1 = min(r for r,c in winner),max(r for r,c in winner)
    c0,c1 = min(c for r,c in winner),max(c for r,c in winner)
    return [list(row[c0:c1+1]) for row in grid[r0:r1+1]]
