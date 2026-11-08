"""Independent model and sampler for public ARC parent e87109e9.

A square color-8 source emits four square-width rays.  Each solid colored
obstacle consults the top legend and turns the ray left or right.  The output
removes the legend and paints every traversed background cell color 8.
"""
from __future__ import annotations
import random
from collections import Counter

RIVALS=(
    'identity','opposite_mode','all_left','all_right','stop_on_hit',
    'straight_through','up_only','horizontal_only','seed_size_one',
    'first_turn_only','paint_obstacles','legend_order_parity',
)
OBJECT_COLORS=(1,2,3,4,6,7,9)


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')
    return value


def grid_copy(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
            or not 1<=len(grid[0])<=30 or any(type(row) is not list
            or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row)
            for row in grid)):
        raise ValueError('Expected a rectangular integer-color grid within 30x30')
    return [row[:] for row in grid]


def analyze(grid):
    g=grid_copy(grid);H,W=len(g),len(g[0])
    if H<12 or W%6 or W<24: raise ValueError('Expected a six-row legend with 4 or 5 tiles')
    border=g[0][0]
    if any(v!=border for v in g[0]+g[5]): raise ValueError('Legend horizontal frame is not uniform')
    mapping={};order=[]
    for i in range(W//6):
        base=i*6
        if any(g[r][base]!=border or g[r][base+5]!=border for r in range(6)):
            raise ValueError('Legend tile frame is not uniform')
        colored=[(r,c,g[r][base+c]) for r in range(1,5) for c in range(1,5)
                 if g[r][base+c] not in (0,border)]
        colors={v for _,_,v in colored};cols={c for _,c,_ in colored}
        if len(colors)!=1 or len(colored)!=4 or cols not in ({1},{4}):
            raise ValueError('Each legend tile must contain one four-cell edge bar')
        color=next(iter(colors));side='left' if cols=={1} else 'right'
        if color in mapping: raise ValueError('Legend colors must be unique')
        mapping[color]=side;order.append(color)
    scene=[row[:] for row in g[6:]];sh=len(scene)
    counts=Counter(v for row in scene for v in row if v!=8)
    if not counts: raise ValueError('Scene background missing')
    bg=counts.most_common(1)[0][0]
    seed={(r,c) for r in range(sh) for c in range(W) if scene[r][c]==8}
    if not seed: raise ValueError('Color-8 source missing')
    r0=min(r for r,c in seed);r1=max(r for r,c in seed);c0=min(c for r,c in seed);c1=max(c for r,c in seed)
    s=r1-r0+1
    if s!=c1-c0+1 or seed!={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}:
        raise ValueError('Color-8 source must be a solid square')
    obstacles={v for row in scene for v in row if v not in (bg,8)}
    if not obstacles or not obstacles<=set(mapping): raise ValueError('Every obstacle color must have a legend command')
    return {'grid':g,'scene':scene,'H':H,'W':W,'sh':sh,'bg':bg,'mapping':mapping,
            'legend_order':order,'seed_cells':seed,'seed_top':(r0,c0),'seed_size':s,
            'obstacle_colors':obstacles}


def _turn(dr,dc,side):
    return (-dc,dr) if side=='left' else (dc,-dr)


def trace(grid,mode='legend',rival=None):
    if mode not in ('legend','opposite'): raise ValueError('Unknown turn policy')
    if rival is not None and rival not in RIVALS: raise ValueError('Unknown rival')
    a=analyze(grid);scene=a['scene'];H,W=a['sh'],a['W'];bg=a['bg'];mapping=dict(a['mapping'])
    if rival=='opposite_mode': mode='opposite' if mode=='legend' else 'legend'
    if rival=='all_left': mapping={c:'left' for c in mapping}
    if rival=='all_right': mapping={c:'right' for c in mapping}
    if rival=='legend_order_parity': mapping={c:('left' if i%2==0 else 'right') for i,c in enumerate(a['legend_order'])}
    s=1 if rival=='seed_size_one' else a['seed_size'];r0,c0=a['seed_top']
    starts=[(-1,0),(1,0),(0,-1),(0,1)]
    if rival=='up_only': starts=[(-1,0)]
    if rival=='horizontal_only': starts=[(0,-1),(0,1)]
    marks=set(a['seed_cells']);records=[]
    for initial in starts:
        r,c=r0,c0;dr,dc=initial;seen=set();turns=0
        while True:
            state=(r,c,dr,dc)
            if state in seen: break
            seen.add(state)
            here={(rr,cc) for rr in range(r,r+s) for cc in range(c,c+s) if 0<=rr<H and 0<=cc<W}
            marks|=here
            nr,nc=r+dr,c+dc
            if nr<0 or nc<0 or nr+s>H or nc+s>W: break
            hits={scene[rr][cc] for rr in range(nr,nr+s) for cc in range(nc,nc+s)
                  if scene[rr][cc] not in (bg,8)}
            if hits:
                color=min(hits)
                if rival=='stop_on_hit' or (rival=='first_turn_only' and turns>=1): break
                if rival=='straight_through':
                    r,c=nr,nc;continue
                side=mapping[color]
                if mode=='opposite': side='right' if side=='left' else 'left'
                ndr,ndc=_turn(dr,dc,side);records.append({'position':[r,c],'incoming':[dr,dc],
                    'color':color,'legend_turn':mapping[color],'applied_turn':side,'outgoing':[ndr,ndc]})
                dr,dc=ndr,ndc;turns+=1
            else:
                r,c=nr,nc
    return a,marks,records,rival


def solve(grid,mode='legend',rival=None):
    a,marks,records,_=trace(grid,mode,rival)
    if rival=='identity': return grid_copy(a['scene'])
    out=grid_copy(a['scene'])
    for r,c in marks:
        if rival=='paint_obstacles' or out[r][c]==a['bg']: out[r][c]=8
    return out


def _profile(kind,index,difficulty='medium'):
    if kind=='demo':
        return [(18,24,2),(20,24,2),(20,24,3),(22,24,2),(24,24,3),(24,24,2)][index]
    if kind=='query': return [(18,24,2),(20,24,3),(22,24,2),(24,30,3)][index]
    return {'easy':(18,24,2),'medium':(22,24,2),'hard':(24,30,3)}[difficulty]


def _paint_rect(scene,box,color):
    r0,c0,r1,c1=box
    if not (0<=r0<=r1<len(scene) and 0<=c0<=c1<len(scene[0])): raise ValueError('Obstacle outside scene')
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):
            if scene[r][c]!=scene[0][0]: raise ValueError('Overlapping construction')
            scene[r][c]=color


def sample_input(seed,index,kind='demo',difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if kind not in ('demo','query','base'): raise ValueError('Unknown input stream')
    if difficulty not in ('easy','medium','hard'): raise ValueError('Unknown difficulty')
    if kind=='demo' and index>5: raise ValueError('Demo source index must be 0..5')
    if kind=='query' and index>3: raise ValueError('Query source index must be 0..3')
    H,W,s=_profile(kind,index,difficulty);rng=random.Random(f'e87109e9:{seed}:{kind}:{index}:{difficulty}')
    n=W//6;colors=list(OBJECT_COLORS);rng.shuffle(colors);colors=colors[:n]
    bg=next(x for x in (0,1,2,3,4,6,7,9) if x not in colors)
    scene=[[bg]*W for _ in range(H)]
    sr=max(7,min(H-s-7,H//2-s//2));sc=max(8,min(W-s-8,W//2-s//2))
    for r in range(sr,sr+s):
        for c in range(sc,sc+s): scene[r][c]=8
    # Role order N,S,W,E,(secondary).  East always turns left into the
    # secondary obstacle, creating a genuine two-collision trace.
    turns=['left','right','right','left']+(['right'] if n==5 else [])
    role_colors=colors[:]
    north=(max(1,sr-6),max(1,sc-s),max(1,sr-4),min(W-2,sc+2*s-1))
    south=(min(H-4,sr+s+4),max(1,sc-s),min(H-2,sr+s+6),min(W-2,sc+2*s-1))
    west=(max(1,sr-s),max(1,sc-7),min(H-2,sr+2*s-1),max(1,sc-5))
    east=(max(1,sr-s),min(W-4,sc+s+5),min(H-2,sr+2*s-1),min(W-2,sc+s+7))
    boxes=[north,south,west,east]
    for box,color in zip(boxes,role_colors[:4]): _paint_rect(scene,box,color)
    east_start=east[1]
    secondary_color=role_colors[4] if n==5 else role_colors[0]
    secondary=(0,max(1,east_start-s),min(s-1,H-2),min(W-2,east_start+s-1))
    _paint_rect(scene,secondary,secondary_color)
    mapping={color:turn for color,turn in zip(role_colors,turns)}
    if n==4: mapping[secondary_color]=turns[0]
    order=role_colors[:]
    if kind=='demo' and index<2:
        # The minimum lesson must not let legend position stand in for the
        # encoded bar direction.  Put the two left-turn roles next to each
        # other, followed by the two right-turn roles; both groups are hit by
        # the four initial rays.  Pair order still varies with the seed.
        left_pair=[role_colors[0],role_colors[3]]
        right_pair=[role_colors[1],role_colors[2]]
        if (seed+index)%2:
            left_pair.reverse();right_pair.reverse()
        order=left_pair+right_pair+role_colors[4:]
    else:
        rng.shuffle(order)
    legend=[[5]*W for _ in range(6)]
    for tile,color in enumerate(order):
        base=tile*6
        for r in range(1,5):
            for c in range(1,5): legend[r][base+c]=0
        lc=1 if mapping[color]=='left' else 4
        for r in range(1,5): legend[r][base+lc]=color
    return legend+scene
