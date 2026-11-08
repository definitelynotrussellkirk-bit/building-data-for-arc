"""Reconstruct occluded rectangle outlines; standalone input-only generator.

Compatibility caveat: restart_hidden fits the supplied labels, including the
train[2] eight-cell stripe-phase discrepancy. It is an explicit phase convention,
not a claim that the supplied labels follow ordinary periodic continuation.

The largest closed green frame is the window. Other closed green frames are
ignored decoys. Rectangle palettes are disjoint, with solid or checker-parity
borders. Each rectangle exposes all four bounding extrema outside the window.
"""
from __future__ import annotations
from collections import Counter
import random

RULE_TASK_ID = 'ee_a6f40cea'


def components(g, same=True, diagonal=False, background=None):
    h,w=len(g),len(g[0]);seen=set();result=[]
    for r in range(h):
        for c in range(w):
            if (r,c) in seen or g[r][c]==background:continue
            stack=[(r,c)];seen.add((r,c));cells=[];color=g[r][c]
            while stack:
                x,y=stack.pop();cells.append((x,y))
                for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))+(((-1,-1),(-1,1),(1,-1),(1,1)) if diagonal else ()):
                    a,b=x+dx,y+dy
                    if 0<=a<h and 0<=b<w and (a,b) not in seen and g[a][b]!=background and (not same or g[a][b]==color):
                        seen.add((a,b));stack.append((a,b))
            result.append(sorted(cells))
    return result


def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def inside(p,b):
    return b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]


def rim(b):
    a,b0,z,d=b
    return [(r,c) for r in range(a,z+1) for c in range(b0,d+1) if r in (a,z) or c in (b0,d)]


def records(g):
    if not g or not g[0] or any(len(row)!=len(g[0]) for row in g):raise ValueError('rectangular nonempty grid required')
    bg=Counter(g[r][c] for r,c in rim((0,0,len(g)-1,len(g[0])-1))).most_common(1)[0][0]
    green=[[3 if v==3 else -1 for v in row] for row in g]
    frames=[]
    for cells in components(green,background=-1):
        b=bbox(cells)
        if b[2]-b[0]>=2 and b[3]-b[1]>=2 and all(g[r][c]==3 for r,c in rim(b)):
            frames.append(b)
    if not frames:raise ValueError('no green rectangular window')
    frame=max(frames,key=lambda b:(b[2]-b[0]+1)*(b[3]-b[1]+1))
    window=(frame[0]+1,frame[1]+1,frame[2]-1,frame[3]-1)
    base=[row[window[1]:window[3]+1] for row in g[window[0]:window[2]+1]]
    external={(r,c):v for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg and not any(inside((r,c),b) for b in frames)}
    # Color adjacency links the two phases of a patterned border. Same colors
    # are global labels, so disconnected visible fragments reunite here.
    colors=sorted(set(external.values()));groups=[];seen=set()
    graph={v:{v} for v in colors}
    for (r,c),v in external.items():
        for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if p in external:
                u=external[p];graph[v].add(u);graph[u].add(v)
    for v in colors:
        if v in seen:continue
        stack=[v];pal=set()
        while stack:
            x=stack.pop()
            if x in pal:continue
            pal.add(x);stack.extend(graph[x]-pal)
        seen|=pal;groups.append(pal)
    items=[]
    for pal in groups:
        visible=[p for p,v in external.items() if v in pal];b=bbox(visible)
        if b[2]-b[0]<1 or b[3]-b[1]<1:continue
        phase=[]
        for parity in (0,1):
            choices=[external[p] for p in visible if sum(p)%2==parity]
            if not choices:choices=[external[p] for p in visible]
            phase.append(Counter(choices).most_common(1)[0][0])
        hidden=[p for p in rim(b) if inside(p,window)]
        if hidden:items.append({'bbox':b,'palette':sorted(pal),'phase':phase,'visible':visible,'hidden':hidden,'hidden_size':len(hidden)})
    return window,base,items


def solve(g,policy='restart_hidden',rival=None):
    if policy not in ('restart_hidden','continue_visible'):raise ValueError('unknown phase policy')
    window,out,items=records(g)
    if rival=='empty':return out
    if rival in ('first','last','most_visible','largest_box') and items:
        key={'first':lambda x:-x['bbox'][0]*100-x['bbox'][1],
             'last':lambda x:x['bbox'][0]*100+x['bbox'][1],
             'most_visible':lambda x:len(x['visible']),
             'largest_box':lambda x:(x['bbox'][2]-x['bbox'][0]+1)*(x['bbox'][3]-x['bbox'][1]+1)}[rival]
        items=[max(items,key=key)]
    for x in items:
        a,b,z,d=x['bbox']
        hidden=x['hidden']
        if rival=='filled_box':hidden=[(r,c) for r in range(a,z+1) for c in range(b,d+1) if inside((r,c),window)]
        origin=sum(x['hidden'][0])
        for r,c in hidden:
            if rival=='solid_low':v=min(x['palette'])
            elif rival=='solid_high':v=max(x['palette'])
            elif policy=='continue_visible':v=x['phase'][(r+c)%2]
            else:v=x['palette'][(r+c-origin)%len(x['palette'])]
            out[r-window[0]][c-window[1]]=v
    return out


def scene(seed,index):
    """Construct the scene independently of the output policy; no label search."""
    rng=random.Random(f'a6f40cea:{seed}:{index}')
    h,w=((20,22),(23,24),(27,28),(30,30))[index%4]
    if index==9:h=w=30
    fr=(4,4,h-5,w-5);mr=(fr[0]+fr[2])//2;mc=(fr[1]+fr[3])//2
    available=[v for v in range(10) if v!=3];rng.shuffle(available)
    bg,fill=available[:2];pool=available[2:]
    count=3+(index%3==2)
    boxes=[(rng.randrange(0,2),1,fr[0]+rng.randrange(2,4),mc-rng.randrange(1,3)),
           (1,mc+2,fr[0]+rng.randrange(2,4),w-1),
           (mr+2,1,h-1,mc-rng.randrange(0,2)),
           (mr+2,mc+2,h-2,w-2)][:count]
    # Two patterned sources and one/two solid sources fit the ten-color palette.
    palettes=[sorted(pool[:2]),sorted(pool[2:4]),[pool[4]],[pool[5]]][:count]
    rng.shuffle(palettes)
    g=[[bg]*w for _ in range(h)];window=(fr[0]+1,fr[1]+1,fr[2]-1,fr[3]-1)
    for k,(box,pal) in enumerate(zip(boxes,palettes)):
        concealed=sorted(p for p in rim(box) if inside(p,window))
        # At least one stripe explicitly teaches restart versus true continuation.
        origin=sum(concealed[0]);flip=1 if len(pal)==2 else 0
        if index%4==2 and k%2:flip=0
        for r,c in rim(box):g[r][c]=pal[(r+c-origin+flip)%len(pal)]
    for r in range(fr[0],fr[2]+1):
        for c in range(fr[1],fr[3]+1):g[r][c]=3 if (r,c) in rim(fr) else fill
    # Isolated small green decoy, containing a non-source color, is excluded.
    if index%2:
        b=(0,mc-1,2,mc+1)
        for r in range(b[0],b[2]+1):
            for c in range(b[1],b[3]+1):g[r][c]=3 if (r,c) in rim(b) else fill
    # Vary orientation without relying on ordinal in any emitted public payload.
    if index%2:g=[list(row) for row in zip(*g)]
    if rng.randrange(2):g=g[::-1]
    if rng.randrange(2):g=[row[::-1] for row in g]
    return g


def generate(seed=0,sample_index=0,difficulty='medium'):
    if type(seed) is not int or type(sample_index) is not int or sample_index<0:raise ValueError('exact integer seed and nonnegative index required')
    return scene(seed,sample_index)


def self_check(g,difficulty='medium'):
    try:
        if not 1<=len(g)<=30 or not 1<=len(g[0])<=30:raise ValueError('size outside 1..30')
        if any(type(v) is not int or not 0<=v<=9 for row in g for v in row):raise ValueError('colors must be exact integers')
        window,base,items=records(g)
        if not items:raise ValueError('no reconstructed source')
        if any(len(x['palette']) not in (1,2) or not set(x['visible'])<=set(rim(x['bbox'])) for x in items):raise ValueError('invalid border palette or geometry')
        return []
    except (ValueError,IndexError,TypeError) as exc:return [str(exc)]
