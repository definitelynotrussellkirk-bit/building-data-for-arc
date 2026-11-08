"""Standalone solver inferred/implemented from the visible review challenge.

Prior rule exposure is disclosed in SOLVE_NOTES.md. No reference/project import.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if (not isinstance(grid,(list,tuple)) or not grid
            or not isinstance(grid[0],(list,tuple)) or not grid[0]):
        raise ValueError('expected a nonempty rectangular grid')
    height,width=len(grid),len(grid[0])
    if any(not isinstance(row,(list,tuple)) or len(row)!=width for row in grid):
        raise ValueError('rows must have equal width')
    if any(type(value) is not int or not 0<=value<=9 for row in grid for value in row):
        raise ValueError('cell colors must be integers from 0 through 9')
    visited=set()
    boxes=[]
    for row in range(height):
        for col in range(width):
            if grid[row][col]==0 or (row,col) in visited:
                continue
            color=grid[row][col]
            stack=[(row,col)];visited.add((row,col))
            top=bottom=row;left=right=col
            while stack:
                r,c=stack.pop()
                top=min(top,r);bottom=max(bottom,r)
                left=min(left,c);right=max(right,c)
                for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if (0<=rr<height and 0<=cc<width and (rr,cc) not in visited
                            and grid[rr][cc]==color):
                        visited.add((rr,cc));stack.append((rr,cc))
            boxes.append((top,left,bottom,right))
    if not boxes:
        raise ValueError('expected at least one nonzero component')
    boxes.sort(key=lambda b:(b[1],b[0]))
    output_width=max(right-left+1 for top,left,bottom,right in boxes)
    output=[]
    for top,left,bottom,right in boxes:
        if output:
            output.append([0]*output_width)
        crop_width=right-left+1
        pad=(output_width-crop_width)//2
        for row in range(top,bottom+1):
            output.append([0]*pad+list(grid[row][left:right+1])
                          +[0]*(output_width-pad-crop_width))
    return output
