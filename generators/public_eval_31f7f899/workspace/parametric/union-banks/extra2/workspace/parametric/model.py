"""Centered bars on a cyan axis: extract geometry, reorder heights, redraw.

The strict validator admits a single straight axis and solid bars centered on the axis (even heights have the upper extra cell).
Different separated bars may share a color. No lookup of parent examples.
"""
from __future__ import annotations
MODES=('ascending','descending')


def checked_grid(grid):
    if not isinstance(grid,list) or not 1<=len(grid)<=30 or not all(isinstance(row,list)for row in grid):
        raise ValueError('grid must have 1..30 list rows')
    width=len(grid[0])
    if not 1<=width<=30 or any(len(row)!=width for row in grid):
        raise ValueError('grid must be rectangular and 1..30 columns')
    if any(type(v)is not int or not 0<=v<=9 for row in grid for v in row):
        raise ValueError('cells must be integer colors 0..9, not booleans')
    return grid


def transpose(grid):
    return [list(row)for row in zip(*grid)]


def analyze(grid):
    checked_grid(grid)
    axis_cells=[(r,c)for r,row in enumerate(grid)for c,v in enumerate(row)if v==6]
    rows={r for r,c in axis_cells};cols={c for r,c in axis_cells}
    if len(rows)==1 and len(cols)>=2:vertical=False
    elif len(cols)==1 and len(rows)>=2:vertical=True
    else:raise ValueError('axis requires at least two collinear cyan cells')
    oriented=transpose(grid)if vertical else [row[:]for row in grid]
    axis=next(r for r,row in enumerate(oriented)if 6 in row)
    bars=[];c=0;w=len(oriented[0])
    while c<w:
        color=oriented[axis][c]
        if color in (6,8):c+=1;continue
        start=c
        while c<w and oriented[axis][c]==color:c+=1
        end=c-1
        top=axis;bottom=axis
        while top>0 and all(oriented[top-1][j]==color for j in range(start,c)):top-=1
        while bottom+1<len(oriented) and all(oriented[bottom+1][j]==color for j in range(start,c)):bottom+=1
        if axis-top not in (bottom-axis,bottom-axis+1):raise ValueError('bar must be centered, with upper extra cell for even heights')
        bars.append({'color':color,'left':start,'right':end,'width':c-start,'height':bottom-top+1})
    if len(bars)<2:raise ValueError('at least two bars required')
    return {'vertical':vertical,'axis':axis,'height':len(oriented),'width':w,'bars':bars}


def render(data,heights):
    bars=data['bars'];heights=list(heights)
    if len(heights)!=len(bars):raise ValueError('one height per bar required')
    h,w,axis=data['height'],data['width'],data['axis']
    if any(type(t)is not int or not (1<=t<=h and axis-t//2>=0 and axis-t//2+t<=h)for t in heights):
        raise ValueError('centered height does not fit canvas')
    out=[[8]*w for _ in range(h)];out[axis]=[6]*w
    for bar,height in zip(bars,heights):
        for r in range(axis-height//2,axis-height//2+height):
            for c in range(bar['left'],bar['right']+1):out[r][c]=bar['color']
    return transpose(out)if data['vertical']else out


def validate(grid):
    data=analyze(grid)
    if render(data,[b['height']for b in data['bars']])!=grid:
        raise ValueError('extra pixels, holes, axis gaps, or nonrectangular bars')
    return data


def solve(grid,mode='ascending'):
    if mode not in MODES:raise ValueError('unknown height order')
    data=validate(grid)
    heights=sorted((b['height']for b in data['bars']),reverse=mode=='descending')
    return render(data,heights)
