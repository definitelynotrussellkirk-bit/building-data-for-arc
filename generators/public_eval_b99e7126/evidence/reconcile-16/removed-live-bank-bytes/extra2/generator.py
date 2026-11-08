"""Decode a repeated micro-mask and complete its uniquely aligned macro copy."""
from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
import random

POLICIES=('complete','fill_holes','identity','bounding_box','partial_bbox','transpose',
          'rotate90','rotate180','other_color_mask','fill_before','eight_holes')
D4=((-1,0),(1,0),(0,-1),(0,1))
D8=tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)

def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
        any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected exact-integer rectangular ARC grid bounded by 30')

def runs(indices):
    groups=[]
    for i in indices:
        if not groups or i!=groups[-1][-1]+1:groups.append([])
        groups[-1].append(i)
    return groups

def holes(occupied,h,w,diagonal=False):
    free={(r,c) for r in range(h) for c in range(w)}-set(occupied)
    seen={p for p in free if p[0] in (0,h-1) or p[1] in (0,w-1)};todo=deque(seen)
    while todo:
        r,c=todo.popleft()
        for dr,dc in (D8 if diagonal else D4):
            q=(r+dr,c+dc)
            if q in free and q not in seen:seen.add(q);todo.append(q)
    return free-seen

def alignments(mask,observed,mh,mw,th,tw):
    return [(r,c) for r in range(mh-th+1) for c in range(mw-tw+1)
            if set(observed)<={(r+u,c+v) for u,v in mask}]

def parse(g):
    grid_check(g);h,w=len(g),len(g[0]);sep=g[0][0]
    row_runs=runs([r for r in range(h) if any(v!=sep for v in g[r])])
    col_runs=runs([c for c in range(w) if any(g[r][c]!=sep for r in range(h))])
    if (not row_runs or not col_runs or len({len(r) for r in row_runs})!=1 or len({len(c) for c in col_runs})!=1 or
        row_runs[0][0]==0 or row_runs[-1][-1]==h-1 or col_runs[0][0]==0 or col_runs[-1][-1]==w-1):
        raise ValueError('regular fully framed tile lattice required')
    th,tw=len(row_runs[0]),len(col_runs[0]);mh,mw=len(row_runs),len(col_runs)
    tiles={(r,c):tuple(tuple(g[u][v] for v in cc) for u in rr)
           for r,rr in enumerate(row_runs) for c,cc in enumerate(col_runs)}
    counts=Counter(tiles.values())
    if len(counts)!=2:raise ValueError('exactly two repeated tile types required')
    ranked=counts.most_common()
    if ranked[0][1]<=ranked[1][1]:raise ValueError('normal tile must be the unique majority')
    normal,special=ranked[0][0],ranked[1][0]
    novel={v for row in special for v in row}-{v for row in normal for v in row}-{sep}
    if len(novel)!=1:raise ValueError('special tile must have one novel foreground color')
    color=next(iter(novel));mask={(r,c) for r,row in enumerate(special) for c,v in enumerate(row) if v==color}
    observed={p for p,tile in tiles.items() if tile==special}
    placements=alignments(mask,observed,mh,mw,th,tw)
    if len(placements)!=1:raise ValueError('template translation must be unique')
    anchor=placements[0];target={(anchor[0]+r,anchor[1]+c) for r,c in mask}
    return {'separator':sep,'row_runs':row_runs,'col_runs':col_runs,'normal':[list(row) for row in normal],
            'special':[list(row) for row in special],'color':color,'mask':mask,'observed':observed,
            'anchor':anchor,'target':target,'shape':(mh,mw),'tile_shape':(th,tw)}

def predict(g,policy='complete'):
    if policy not in POLICIES:raise ValueError('unknown completion policy')
    cert=parse(g)
    if policy=='identity':return deepcopy(g)
    mh,mw=cert['shape'];th,tw=cert['tile_shape'];ar,ac=cert['anchor'];mask=cert['mask'];target=set(cert['target'])
    if policy=='fill_holes':target|=holes(target,mh,mw)
    elif policy=='fill_before':target|=holes(cert['observed'],mh,mw)
    elif policy=='eight_holes':target|=holes(target,mh,mw,diagonal=True)
    elif policy=='bounding_box':target={(ar+r,ac+c) for r in range(th) for c in range(tw)}
    elif policy=='partial_bbox':
        ar=min(r for r,c in cert['observed']);ac=min(c for r,c in cert['observed'])
        target={(ar+r,ac+c) for r,c in mask if ar+r<mh and ac+c<mw}
    elif policy=='transpose':target={(ar+c,ac+r) for r,c in mask if ar+c<mh and ac+r<mw}
    elif policy=='rotate90':target={(ar+c,ac+th-1-r) for r,c in mask if ar+c<mh and ac+th-1-r<mw}
    elif policy=='rotate180':target={(ar+th-1-r,ac+tw-1-c) for r,c in mask}
    elif policy=='other_color_mask':target={(ar+r,ac+c) for r in range(th) for c in range(tw) if (r,c) not in mask}
    out=deepcopy(g)
    for r,c in target:
        for u,rr in enumerate(cert['row_runs'][r]):
            for v,cc in enumerate(cert['col_runs'][c]):out[rr][cc]=cert['special'][u][v]
    return out

MASKS=(('011','101','111'),('1110','1010','1111','0001'),('101','101','111'),
       ('101','111','101'),('010','111','101'),('1111','1001','1001','1111'),
       ('010','101','111'),('110','001','010'),('1101','1001','1111','0010'),
       ('111','101','111'))

def transform(g,pose):
    out=deepcopy(g)
    if pose>=4:out=[row[::-1] for row in out]
    for _ in range(pose%4):out=[list(row) for row in zip(*out[::-1])]
    return out

def _scene(seed,index):
    rng=random.Random(f'b99e7126:scene:{seed}:{index}')
    mask_lines=MASKS[index];th=len(mask_lines);tw=len(mask_lines[0]);mask={(r,c) for r,row in enumerate(mask_lines) for c,v in enumerate(row) if v=='1'}
    if index==9:mh=mw=7;top=left=2;bottom=right=1
    else:
        mh=rng.randint(max(th,4),min(6,28//(th+1)))
        mw=rng.randint(max(tw,4),min(6,28//(tw+1)))
        top=left=bottom=right=1
        if index==1 and mh*mw<=16:mh=5
    # The 30x30 query duplicates the top/left separator band, not data pixels.
    h=top+mh*th+(mh-1)+bottom;w=left+mw*tw+(mw-1)+right
    sep,bg,detail,novel=rng.sample(list(range(10)),4)
    normal=[[bg if (r+c+seed+index)%3 else detail for c in range(tw)] for r in range(th)]
    special=[[novel if (r,c) in mask else bg for c in range(tw)] for r in range(th)]
    ar=rng.randrange(mh-th+1);ac=rng.randrange(mw-tw+1)
    target={(ar+r,ac+c) for r,c in mask}
    if index==0:partial={(1,2),(2,0),(2,1),(2,2)}
    elif index==1:partial={(r,c) for r in range(3) for c in range(3) if (r,c)!=(1,1)}
    elif index==9:partial={(0,1),(2,0),(2,1),(2,2)}
    else:
        for _ in range(200):
            count=rng.randint(2,min(len(mask)-1,(mh*mw-1)//2));partial=set(rng.sample(sorted(mask),count))
            observed={(ar+r,ac+c) for r,c in partial}
            if len(alignments(mask,observed,mh,mw,th,tw))==1:break
        else:raise ValueError('unique partial-template construction exhausted')
    observed={(ar+r,ac+c) for r,c in partial}
    if len(alignments(mask,observed,mh,mw,th,tw))!=1:raise AssertionError('teaching partial is ambiguous')
    g=[[sep]*w for _ in range(h)]
    for r in range(mh):
        for c in range(mw):
            tile=special if (r,c) in observed else normal
            for u in range(th):
                for v in range(tw):g[top+r*(th+1)+u][left+c*(tw+1)+v]=tile[u][v]
    pose=rng.choice((0,3,4,7)) if index==0 else rng.randrange(8)
    g=transform(g,pose);cert=parse(g)
    return g,{'profile':index,'pose':pose,'micro_shape':list(cert['tile_shape']),
              'macro_shape':list(cert['shape']),'observed_count':len(cert['observed']),
              'complete_count':len(cert['target']),'cavity_count':len(holes(cert['target'],*cert['shape'])),
              'initial_cavity_count':len(holes(cert['observed'],*cert['shape']))}

@lru_cache(maxsize=128)
def bank(seed):
    scenes=[_scene(seed,i) for i in range(10)]
    if len({str(g) for g,m in scenes})!=10:raise ValueError('duplicate bank input')
    return scenes

RULE_TASK_ID = 'ee_b99e7126'
EXAMPLES_NEEDED = 2

def generate(seed=0,sample_index=0,difficulty='medium',**kwargs):
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:
        raise ValueError('nonnegative exact integer seed/index required')
    if difficulty not in ('easy','medium','hard','mixed'):
        raise ValueError('unknown difficulty')
    grid,meta=_scene(seed+sample_index//10,sample_index%10)
    return {'input':deepcopy(grid),'metadata':deepcopy(meta)}

def self_check(grid,**kwargs):
    try:
        parse(grid);predict(grid,'complete')
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
