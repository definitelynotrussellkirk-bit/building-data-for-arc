"""Inferred from the five visible examples; no generator/reference imports."""

def solve(grid):
    if not grid:
        return []
    height=len(grid)
    width=len(grid[0])
    output=[[0 for _ in range(width)] for _ in range(height)]
    for col in range(width):
        destination=height-1
        for row in range(height-1,-1,-1):
            color=grid[row][col]
            if color==8:
                output[row][col]=8
                destination=row-1
            elif color!=0:
                output[destination][col]=color
                destination-=1
    return output
