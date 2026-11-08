"""Independent Python claims for chamber-local majority and contact aggregation."""
from __future__ import annotations
from collections import Counter

DIRECTIONS=((-1,0),(1,0),(0,-1),(0,1))

def validate(grid):
    if type(grid) is not list or not grid or len(grid)>30:
        raise ValueError('grid must be a nonempty list with at most 30 rows')
    if type(grid[0]) is not list or not grid[0] or len(grid[0])>30:
        raise ValueError('grid width must be 1..30')
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('rectangular exact-integer color grid required')

def mode(values):
    counts=Counter(values)
    if not counts:raise ValueError('empty vote')
    return min(counts,key=lambda v:(-counts[v],v))

def components(cells):
    remaining=set(cells);out=[]
    while remaining:
        start=min(remaining);remaining.remove(start);todo=[start];component=[]
        while todo:
            r,c=todo.pop();component.append((r,c))
            for dr,dc in DIRECTIONS:
                p=(r+dr,c+dc)
                if p in remaining:remaining.remove(p);todo.append(p)
        out.append(sorted(component))
    return out

def area(cells):
    return (max(r for r,c in cells)-min(r for r,c in cells)+1)*(max(c for r,c in cells)-min(c for r,c in cells)+1)

def analyze(grid):
    validate(grid);h,w=len(grid),len(grid[0]);bg=mode(v for row in grid for v in row)
    colored=[]
    for color in sorted(set(v for row in grid for v in row)-{bg}):
        for cells in components((r,c) for r in range(h) for c in range(w) if grid[r][c]==color):
            colored.append((area(cells),min(cells),color,cells))
    if not colored:raise ValueError('missing wiring network')
    # The wire is the spatially spanning monochrome network, not a palette rank.
    colored.sort(key=lambda item:(-item[0],item[1]))
    wire=colored[0][2]
    hubs=[(r,c) for r in range(1,h-1) for c in range(1,w-1)
          if all(grid[r+dr][c+dc]==wire for dr in (-1,0,1) for dc in (-1,0,1))]
    if len(hubs)!=1:raise ValueError('expected a unique solid 3x3 wiring hub')
    hr,hc=hubs[0];hub={(hr+dr,hc+dc) for dr in (-1,0,1) for dc in (-1,0,1)}
    groups=components((r,c) for r in range(h) for c in range(w) if grid[r][c]!=bg and (r,c) not in hub)
    terminals=[]
    for cells in groups:
        pigments=[grid[r][c] for r,c in cells if grid[r][c]!=wire]
        if not pigments:raise ValueError('unconnected wire-only branch')
        contacts=[(r,c) for r,c in cells if grid[r][c]==wire and any((r+dr,c+dc) in hub for dr,dc in DIRECTIONS)]
        if not contacts:raise ValueError('terminal is not connected to the hub')
        counts=Counter(pigments)
        terminals.append({'cells':cells,'counts':dict(counts),'winner':mode(pigments),
                          'contacts':len(contacts),'contact_cells':contacts,'area':len(pigments)})
    if len(terminals)<3:raise ValueError('at least three terminal chambers required')
    return {'background':bg,'wire':wire,'hub':(hr,hc),'terminals':terminals}

def render(grid,data,aggregation='contacts'):
    if aggregation not in ('contacts','chambers'):raise ValueError('unknown aggregation')
    out=[row[:] for row in grid];votes=[]
    for terminal in data['terminals']:
        color=terminal['winner']
        votes.extend([color]*(terminal['contacts'] if aggregation=='contacts' else 1))
        for r,c in terminal['cells']:
            if grid[r][c]==data['wire']:out[r][c]=color
    r,c=data['hub'];out[r][c]=mode(votes)
    return out

def solve(grid,aggregation='contacts'):
    return render(grid,analyze(grid),aggregation)
