"""Visible-example solution: propagate a region's unique seed through zeros."""
def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected nonempty rectangular grid')
    h,w=len(grid),len(grid[0])
    out=[list(row) for row in grid]
    unseen={(r,c) for r in range(h) for c in range(w) if grid[r][c] != 5}
    while unseen:
        start=min(unseen)
        unseen.remove(start)
        cells=[start]
        for r,c in cells:
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen:
                    unseen.remove(p)
                    cells.append(p)
        colors={grid[r][c] for r,c in cells} - {0}
        if len(colors)>1:
            raise ValueError('Demonstrations do not specify competing seeds in one region')
        if colors:
            color=next(iter(colors))
            for r,c in cells:
                out[r][c]=color
    return out
