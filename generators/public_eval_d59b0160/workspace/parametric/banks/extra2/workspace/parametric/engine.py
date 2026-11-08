"""Three-color panel filtering and a missing-key relay family."""
from __future__ import annotations
from collections import Counter, deque
import hashlib
import random

SETTINGS=('filter_only','highlight_closest_survivor')
BG=7
PANEL_BG=0
FRAME=3
HIGHLIGHT=9
N4=((1,0),(-1,0),(0,1),(0,-1))


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list
        or not 1<=len(g[0])<=30 or any(type(row) is not list or len(row)!=len(g[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')


def _inside_key(r,c,key):
    return key['r']<=r<key['r']+4 and key['c']<=c<key['c']+4


def _find_key(g):
    h,w=len(g),len(g[0]);candidates=[]
    for r in range(h-3):
        for c in range(w-3):
            if any(g[r+3][c+j]!=FRAME for j in range(4)):continue
            if any(g[r+i][c+3]!=FRAME for i in range(4)):continue
            markers=[]
            for i in range(3):
                for j in range(3):
                    v=g[r+i][c+j]
                    if v!=BG:markers.append((r+i,c+j,v))
            colors=[v for _,_,v in markers]
            if len(markers)==3 and len(set(colors))==3 and all(v not in (PANEL_BG,FRAME,BG) for v in colors):
                candidates.append({'r':r,'c':c,'markers':markers,'colors':tuple(colors)})
    if len(candidates)!=1:raise ValueError('Expected one 4x4 L-frame key with three distinct markers')
    return candidates[0]


def _components_outside_key(g,key):
    h,w=len(g),len(g[0]);seen=set();out=[]
    for r in range(h):
        for c in range(w):
            if g[r][c]==BG or _inside_key(r,c,key) or (r,c) in seen:continue
            q=deque([(r,c)]);seen.add((r,c));cells=[]
            while q:
                x,y=q.popleft();cells.append((x,y))
                for dr,dc in N4:
                    a,b=x+dr,y+dc
                    if (0<=a<h and 0<=b<w and (a,b) not in seen and
                        not _inside_key(a,b,key) and g[a][b]!=BG):
                        seen.add((a,b));q.append((a,b))
            out.append(cells)
    return out


def analyze(g):
    grid_check(g);key=_find_key(g);keyset=set(key['colors']);panels=[]
    for cells in _components_outside_key(g,key):
        r1=min(r for r,c in cells);r2=max(r for r,c in cells)
        c1=min(c for r,c in cells);c2=max(c for r,c in cells)
        expected={(r,c) for r in range(r1,r2+1) for c in range(c1,c2+1)}
        if set(cells)!=expected:raise ValueError('Every payload panel must be a filled non-background rectangle')
        counts=Counter(g[r][c] for r,c in cells if g[r][c]!=PANEL_BG)
        colors=set(counts)
        missing=len(keyset-colors)
        panels.append({'id':-1,'cells':sorted(cells),'bbox':(r1,c1,r2,c2),'area':len(cells),
                       'colors':colors,'color_counts':counts,'missing':missing})
    panels.sort(key=lambda p:(p['bbox'][0],p['bbox'][1]))
    for i,p in enumerate(panels):p['id']=i
    if len(panels)<3:raise ValueError('Expected at least three rectangular payload panels')
    complete=[p['id'] for p in panels if p['missing']==0]
    survivors=[p for p in panels if p['missing']>0]
    if not complete or not survivors:raise ValueError('Expected both removable and surviving panels')
    best=min(p['missing'] for p in survivors)
    closest=[p['id'] for p in survivors if p['missing']==best]
    return {'height':len(g),'width':len(g[0]),'key':key,'key_colors':tuple(key['colors']),
            'panels':panels,'complete_ids':complete,'survivor_ids':[p['id'] for p in survivors],
            'closest_missing':best,'closest_survivor_ids':closest}


def rivals(finish):
    if finish=='filter_only':
        return ('other_setting','identity','remove_any_key','inverse_filter','exact_key_only','exactly_once')
    if finish=='highlight_closest_survivor':
        return ('other_setting','first_survivor','largest_survivor','most_key_occurrences','wrong_pre_filter')
    raise ValueError('Unknown finish setting')


def _deletion_ids(info,rival):
    keyset=set(info['key_colors'])
    if rival=='remove_any_key':return [p['id'] for p in info['panels'] if p['missing']<len(keyset)]
    if rival=='inverse_filter':return [p['id'] for p in info['panels'] if p['missing']>0]
    if rival=='exact_key_only':return [p['id'] for p in info['panels'] if p['colors']==keyset]
    if rival=='exactly_once':
        return [p['id'] for p in info['panels'] if all(p['color_counts'][k]==1 for k in keyset)]
    return info['complete_ids']


def _selection_ids(info,rival):
    survivors=[p for p in info['panels'] if p['missing']>0]
    if rival=='first_survivor':return [survivors[0]['id']]
    if rival=='largest_survivor':return [max(survivors,key=lambda p:(p['area'],-p['id']))['id']]
    if rival=='most_key_occurrences':
        keys=set(info['key_colors'])
        return [max(survivors,key=lambda p:(sum(p['color_counts'][k] for k in keys),-p['id']))['id']]
    if rival=='wrong_pre_filter':
        best=min(p['missing'] for p in info['panels'])
        return [p['id'] for p in info['panels'] if p['missing']==best]
    return info['closest_survivor_ids']


def solve(g,finish='filter_only',rival=None):
    if finish not in SETTINGS:raise ValueError('Unknown finish setting')
    if rival is not None and rival not in set(rivals(finish)):raise ValueError('Unknown rival')
    if rival=='identity':
        grid_check(g);return [row[:] for row in g]
    if rival=='other_setting':finish=SETTINGS[1-SETTINGS.index(finish)];rival=None
    info=analyze(g);out=[row[:] for row in g]
    deletion=_deletion_ids(info,rival if finish=='filter_only' else None)
    for p in info['panels']:
        if p['id'] in deletion:
            for r,c in p['cells']:out[r][c]=BG
    if finish=='highlight_closest_survivor':
        selected=_selection_ids(info,rival)
        for p in info['panels']:
            if p['id'] in selected:
                for r,c in p['cells']:
                    if g[r][c]!=PANEL_BG:out[r][c]=HIGHLIGHT
    return out


def rival_output(g,finish,name):return solve(g,finish,rival=name)


def _rng(seed,kind,index):
    integer(seed,0,2**63-1,'seed');integer(index,0,5 if kind=='demo' else 3,'index')
    return random.Random(int.from_bytes(hashlib.sha256(f'd59b0160:v1:{seed}:{kind}:{index}'.encode()).digest(),'big'))


def _dimensions(kind,index):
    return ((16,16),(18,20),(20,18),(22,24),(24,26),(26,28))[index] if kind=='demo' else ((18,22),(22,19),(26,25),(30,30))[index]


def _panel_rectangles(h,w):
    mid_h=(h-7)//2;bottom=6+mid_h;bottom_h=h-bottom
    left_w=(w-1)//2;right=left_w+1;right_w=w-right
    rects=[(0,6,4,w-6),(5,0,mid_h,left_w),(5,right,mid_h,right_w),
           (bottom,0,bottom_h,left_w),(bottom,right,bottom_h,right_w)]
    if any(hh<4 or ww<4 for r,c,hh,ww in rects):raise RuntimeError('Canvas too small for constructive panel grammar')
    return rects


def _paint_panel(g,rect,colors,rng):
    r,c,h,w=rect;positions=[(x,y) for x in range(r,r+h) for y in range(c,c+w)]
    if len(colors)>len(positions):raise RuntimeError('Panel marker payload exceeds rectangle')
    rng.shuffle(positions)
    for x in range(r,r+h):
        for y in range(c,c+w):g[x][y]=PANEL_BG
    for (x,y),color in zip(positions,colors):g[x][y]=color


def scene(seed,kind,index):
    if kind not in ('demo','query'):raise ValueError('kind must be demo or query')
    rng=_rng(seed,kind,index);h,w=_dimensions(kind,index);g=[[BG]*w for _ in range(h)]
    key_colors=rng.sample([1,2,4,5,6,8],3)
    marker_positions=rng.sample([(r,c) for r in range(3) for c in range(3)],3)
    for j in range(4):g[3][j]=FRAME
    for i in range(4):g[i][3]=FRAME
    for (r,c),color in zip(marker_positions,key_colors):g[r][c]=color
    decoys=[v for v in (1,2,4,5,6,8,9) if v not in key_colors];rng.shuffle(decoys)
    k0,k1,k2=key_colors
    payloads=[
        [k0]*6+[decoys[0],decoys[1]],                 # first survivor; many occurrences; misses two
        [k0,k1,k2,k0,decoys[0],decoys[1]],           # complete with duplicate and decoys
        [k0,k1,decoys[0]],                            # unique closest survivor; misses one
        [k0,k1,k2],                                   # exact complete panel
        [decoys[0],decoys[1],decoys[2],decoys[0]],    # large no-key survivor
    ]
    for rect,payload in zip(_panel_rectangles(h,w),payloads):_paint_panel(g,rect,payload,rng)
    info=analyze(g)
    if len(info['closest_survivor_ids'])!=1:raise RuntimeError('Constructed closest survivor must be unique')
    chosen=info['panels'][info['closest_survivor_ids'][0]]
    first=info['panels'][info['survivor_ids'][0]]
    largest=max((p for p in info['panels'] if p['missing']>0),key=lambda p:(p['area'],-p['id']))
    most=max((p for p in info['panels'] if p['missing']>0),key=lambda p:(sum(p['color_counts'][k] for k in key_colors),-p['id']))
    if chosen['id'] in (first['id'],largest['id'],most['id']):raise RuntimeError('Constructed proxy separation failed')
    return g


def generate(seed,kind,index):return scene(seed,kind,index)


def self_check(g):
    try:analyze(g)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
