"""Independent claim oracle: a marked side chooses one of two source panels."""
from __future__ import annotations
from collections import deque


def validate(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or any(type(row) is not list for row in grid)
        or not 1<=len(grid[0])<=30 or any(len(row)!=len(grid[0])for row in grid)
        or any(type(v)is not int or not 0<=v<=9 for row in grid for v in row)):
        raise ValueError('Expected rectangular 1..30 exact integer color grid')


def bands(indices):
    result=[]
    for i in indices:
        if not result or i>result[-1][1]+1:result.append([i,i])
        else:result[-1][1]=i
    return result


def flood(start,allowed,diagonal=False):
    allowed=set(allowed)
    if start not in allowed:return set()
    seen={start};q=deque([start])
    steps=[(dr,dc)for dr in (-1,0,1)for dc in (-1,0,1)if (dr or dc) and (diagonal or abs(dr)+abs(dc)==1)]
    while q:
        r,c=q.popleft()
        for dr,dc in steps:
            p=(r+dr,c+dc)
            if p in allowed and p not in seen:seen.add(p);q.append(p)
    return seen


def components(cells,diagonal=False):
    todo=set(cells);parts=[]
    while todo:
        p=min(todo);part=flood(p,todo,diagonal);parts.append(part);todo-=part
    return parts


def analyze(grid):
    validate(grid);h,w=len(grid),len(grid[0]);frame=grid[0][0]
    rb=bands(r for r in range(h)if any(v!=frame for v in grid[r]))
    cb=bands(c for c in range(w)if any(grid[r][c]!=frame for r in range(h)))
    boxes=[(r0,c0,r1,c1)for r0,r1 in rb for c0,c1 in cb]
    if len(boxes)!=4:raise ValueError('Expected four framed panels in reading order')
    shapes={(r1-r0+1,c1-c0+1)for r0,c0,r1,c1 in boxes}
    if len(shapes)!=1:raise ValueError('Panels must have matching dimensions')
    panels=[[[grid[r][c]for c in range(c0,c1+1)]for r in range(r0,r1+1)]for r0,c0,r1,c1 in boxes]
    ph,pw=next(iter(shapes));target=panels[3];bg=target[0][0]
    if any(v!=bg for row in target for v in row):raise ValueError('Destination panel must be blank')
    if bg==frame or any(v==frame for p in panels for row in p for v in row):
        raise ValueError('Frame color must be absent from panel interiors')
    marks={(r,c)for r in range(ph)for c in range(pw)if panels[0][r][c]!=bg}
    colors={panels[0][r][c]for r,c in marks}
    if len(colors)!=1:raise ValueError('One instruction color required')
    parts=components(marks,True)
    if len(parts)!=2:raise ValueError('A divider and a separate singleton hint are required')
    line=max(parts,key=len);hints=marks-line
    if len(line)<3 or len(hints)!=1:raise ValueError('Expected one long divider and one hint')
    domain={(r,c)for r in range(ph)for c in range(pw)}
    regions=components(domain-line)
    if len(regions)!=2:raise ValueError('Divider must separate exactly two 4-connected regions')
    hint=next(iter(hints));selected=flood(hint,domain-line)
    return {'frame':frame,'background':bg,'boxes':boxes,'panels':panels,'shape':(ph,pw),
            'line':sorted(line),'hint':hint,'selected':sorted(selected),
            'regions':[sorted(p)for p in regions]}


def render(grid,data,mode='marker_first',selected=None,boundary='first'):
    if mode not in ('marker_first','marker_second'):raise ValueError('Unknown side assignment')
    if boundary not in ('first','second','background'):raise ValueError('Unknown boundary policy')
    chosen=set(data['selected'] if selected is None else selected);line=set(data['line'])
    bg=data['background'];first,second=data['panels'][1:3]
    top,left,_,_=data['boxes'][3];out=[row[:]for row in grid]
    for r in range(data['shape'][0]):
        for c in range(data['shape'][1]):
            if (r,c)in line:
                a,b=(first[r][c],second[r][c])if boundary=='first'else(second[r][c],first[r][c])
                value=bg if boundary=='background' else a if a!=bg else b
            else:
                take_first=((r,c)in chosen)==(mode=='marker_first')
                value=first[r][c]if take_first else second[r][c]
            out[top+r][left+c]=value
    return out


def solve(grid,mode='marker_first'):
    return render(grid,analyze(grid),mode)
