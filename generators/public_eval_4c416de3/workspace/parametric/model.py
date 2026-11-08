"""Independent Python claim oracle for corner-normalized glyph completion.

The canonical runtime remains Racket. No original grids or labels are loaded here.
"""
from __future__ import annotations
from collections import Counter


def validate(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        any(type(row) is not list for row in grid) or not 1 <= len(grid[0]) <= 30 or
        any(len(row) != len(grid[0]) for row in grid) or
        any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')


def analyze(grid):
    validate(grid)
    h,w=len(grid),len(grid[0])
    counts=Counter(v for row in grid for v in row if v != 0)
    if not counts:raise ValueError('A nonblack background is required')
    bg=min(counts,key=lambda v:(-counts[v],v))
    def black(r,c):return 0 <= r < h and 0 <= c < w and grid[r][c] == 0
    corners=[]
    for r in range(h):
        for c in range(w):
            for sr in (-1,1):
                for sc in (-1,1):
                    if (not black(r-sr,c) and not black(r,c-sc) and
                        sum(black(r+k*sr,c) for k in (1,2,3))>=2 and
                        sum(black(r,c+k*sc) for k in (1,2,3))>=2):
                        corners.append((r,c,sr,sc))
    if not corners:raise ValueError('No supported black-frame corners')
    marks={i:[] for i in range(len(corners))}
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v in (0,bg):continue
            distance=lambda i:((r-corners[i][0])**2+(c-corners[i][1])**2,i)
            i=min(range(len(corners)),key=distance)
            if distance(i)[0]>8:raise ValueError('Colored mark is not near a frame corner')
            marks[i].append((r,c,v))
    groups=[]
    for i,points in marks.items():
        if not points:continue
        r,c,sr,sc=corners[i]
        colors={v for _,_,v in points}
        if len(colors)!=1:raise ValueError('One color per corner is required')
        offsets=sorted(((rr-r)*sr,(cc-c)*sc)for rr,cc,_ in points)
        groups.append({'corner':corners[i],'color':next(iter(colors)),
                       'offsets':offsets,'cells':[(rr,cc)for rr,cc,_ in points]})
    if not groups:raise ValueError('No active marked corners')
    exemplar=max(groups,key=lambda x:len(x['offsets']))
    motif=exemplar['offsets']
    if len(motif)<3:raise ValueError('A completed exemplar is required')
    if any(not set(x['offsets']) <= set(motif) for x in groups):
        raise ValueError('Corner marks disagree with the normalized exemplar')
    return {'background':bg,'corners':corners,'groups':groups,'motif':motif,
            'exemplar_corner':exemplar['corner']}


def render(grid,data,mode='full',motif=None):
    if mode not in ('full','outside'):raise ValueError('Unknown copy extent')
    points=data['motif'] if motif is None else motif
    out=[row[:] for row in grid]
    for group in data['groups']:
        r,c,sr,sc=group['corner']
        for a,b in points:
            if mode=='outside' and a>0 and b>0:continue
            rr,cc=r+sr*a,c+sc*b
            if 0<=rr<len(out) and 0<=cc<len(out[0]):out[rr][cc]=group['color']
    return out


def solve(grid,mode='full'):
    return render(grid,analyze(grid),mode)
