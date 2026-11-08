"""Complete empty centers of same-colored four-arm cardinal crosses.

Authored during the visible-example solve phase. No reference code imported.
Prior rule exposure during generator review is declared in SOLVE_NOTES.md.
"""

def solve(grid):
    if not grid:
        return []
    width=len(grid[0])
    if any(len(row)!=width for row in grid):
        raise ValueError('grid must be rectangular')
    result=[row[:] for row in grid]
    for r in range(1,len(grid)-1):
        for c in range(1,width-1):
            if grid[r][c]!=0:
                continue
            color=grid[r-1][c]
            if color!=0 and grid[r+1][c]==color and grid[r][c-1]==color and grid[r][c+1]==color:
                result[r][c]=color
    return result
