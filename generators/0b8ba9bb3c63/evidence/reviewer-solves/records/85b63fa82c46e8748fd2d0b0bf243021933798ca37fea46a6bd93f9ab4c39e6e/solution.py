"""Visible-example solution for the cyan emitter / transparent-red puzzle."""
def solve(grid):
    height,width=len(grid),len(grid[0])
    cyan=[(r,c) for r in range(height) for c in range(width) if grid[r][c]==8]
    if not cyan:
        raise ValueError("No cyan emitter")
    r0=min(r for r,c in cyan);r1=max(r for r,c in cyan)
    c0=min(c for r,c in cyan);c1=max(c for r,c in cyan)
    result=[list(row) for row in grid]
    for row in range(r0,r1+1):
        for cols in (range(c0-1,-1,-1),range(c1+1,width)):
            for col in cols:
                if grid[row][col] not in (0,2): break
                result[row][col]=4
    for col in range(c0,c1+1):
        for rows in (range(r0-1,-1,-1),range(r1+1,height)):
            for row in rows:
                if grid[row][col] not in (0,2): break
                result[row][col]=4
    return result
