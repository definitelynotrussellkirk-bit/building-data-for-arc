"""Standalone rule inferred from this episode's visible demonstrations."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid,(list,tuple)) or not grid or not grid[0]:
        raise ValueError('Expected a nonempty rectangular grid')
    width=len(grid[0])
    if any(not isinstance(row,(list,tuple)) or len(row)!=width for row in grid):
        raise ValueError('Expected a rectangular grid')
    positions: dict[int,list[tuple[int,int]]] = {}
    for row_index,row in enumerate(grid):
        for col_index,color in enumerate(row):
            if type(color) is not int or not 0<=color<=9:
                raise ValueError('Expected integer colors 0..9')
            if color:
                positions.setdefault(color,[]).append((row_index,col_index))
    answer=[[0]*width for _ in grid]
    for color,cells in positions.items():
        top=min(r for r,c in cells);bottom=max(r for r,c in cells)
        left=min(c for r,c in cells);right=max(c for r,c in cells)
        for c in range(left,right+1):
            answer[top][c]=color
            answer[bottom][c]=color
        for r in range(top,bottom+1):
            answer[r][left]=color
            answer[r][right]=color
    return answer
