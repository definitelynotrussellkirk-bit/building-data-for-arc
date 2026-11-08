"""Native legend-driven rectangle completion with explicit compositing priority."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib
import random
BASE=Path(__file__).resolve().parent
PRIORITIES=('top_priority','bottom_priority')

def validate_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected rectangular 1..30 exact integer grid')

def bbox(cells):
    rr,cc=zip(*cells);return [min(rr),min(cc),max(rr),max(cc)]

def inside(p,b):return b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]

def groups(cells):
    rest=set(cells);result=[]
    while rest:
        p=min(rest);rest.remove(p);part=[p]
        for r,c in part:
            for q in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if q in rest:rest.remove(q);part.append(q)
        result.append(sorted(part))
    return result

def corners(box,diagonal=0):
    r,c,R,C=box
    return ([(r,c),(r,c+1),(r+1,c),(R,C),(R,C-1),(R-1,C)] if diagonal==0
            else [(r,C),(r,C-1),(r+1,C),(R,c),(R,c+1),(R-1,c)])

def measure(g):
    validate_grid(g);h,w=len(g),len(g[0]);freq=Counter(v for row in g for v in row)
    bg=max(freq,key=freq.get)
    tables=[]
    for c in range(w-1):
        for r in range(h):
            if g[r][c]==bg or (r and g[r-1][c]!=bg):continue
            R=r
            while R+1<h and g[R+1][c]!=bg:R+=1
            keys=[g[y][c] for y in range(r,R+1)]
            if len(keys)<2 or len(set(keys))!=len(keys) or not any(g[y][c+1]!=bg for y in range(r,R+1)):continue
            box=[r,c,R,c+1]
            rim=[(y,x) for y in range(max(0,r-1),min(h,R+2)) for x in range(max(0,c-1),min(w,c+3)) if not inside((y,x),box)]
            if all(g[y][x]==bg for y,x in rim):tables.append(box)
    if not tables:raise ValueError('No isolated two-column legend with distinct keys')
    height=max(b[2]-b[0]+1 for b in tables);best=[b for b in tables if b[2]-b[0]+1==height]
    if len(best)!=1:raise ValueError('Ambiguous legend')
    table=best[0];r,c,R,C=table;entries=[[g[y][c],g[y][c+1]] for y in range(r,R+1)]
    layers=[]
    for key,fill_code in entries:
        fill=bg if fill_code==0 else fill_code
        parts=groups([(y,x) for y in range(h) for x in range(w) if g[y][x]==key and not inside((y,x),table)])
        ls=[];solids=[]
        for part in parts:
            b=bbox(part);hh,ww=b[2]-b[0]+1,b[3]-b[1]+1
            if len(part)==3 and hh==ww==2:ls.append(part)
            elif hh>=2 and ww>=2 and len(part)==hh*ww:solids.append(part)
            else:raise ValueError('Mapped color has a malformed L or solid block')
        if ls:
            if len(ls)!=2:raise ValueError('Expected exactly two L corners for a mapped color')
            markers=sorted(ls[0]+ls[1]);b=bbox(markers)
            if set(markers) not in (set(corners(b,0)),set(corners(b,1))):raise ValueError('L corners must be diagonally opposed')
            layers.append({'key':key,'fill':fill,'box':b,'markers':markers})
        for part in solids:layers.append({'key':key,'fill':fill,'box':bbox(part),'markers':[]})
    return {'background':bg,'legend_box':table,'entries':entries,'layers':layers}

def render(g,state,priority='top_priority'):
    if priority not in PRIORITIES:raise ValueError('Unknown priority')
    out=[row[:] for row in g]
    layers=state['layers'][::-1] if priority=='top_priority' else state['layers']
    for layer in layers:
        r,c,R,C=layer['box'];markers={tuple(p) for p in layer['markers']}
        for y in range(r,R+1):
            for x in range(c,C+1):out[y][x]=layer['key'] if (y,x) in markers else layer['fill']
    return out

def solve(g,priority='top_priority'):return render(g,measure(g),priority)

def _setting(settings):
    if type(settings) is not dict or set(settings)!={'priority'} or type(settings['priority']) is not str or settings['priority'] not in PRIORITIES:
        raise ValueError('settings must contain exactly priority=top_priority/bottom_priority')
    return settings['priority']

def program(settings):
    priority=_setting(settings);code=(BASE/'canonical.rkt').read_text()
    return code if priority=='top_priority' else code.replace('(define earlier-wins #t)','(define earlier-wins #f)')

def _rng(seed,label):return random.Random(int.from_bytes(hashlib.sha256(f'9385bd28:{seed}:{label}'.encode()).digest(),'big'))

def sample(seed,index,split='train'):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0 or split not in ('train','test'):
        raise ValueError('Invalid seed/index/split')
    rng=_rng(seed,f'{split}:{index}')
    sizes=[(18,20),(30,30),(20,24),(22,26),(24,28),(26,24)] if split=='train' else [(18,22),(22,24),(26,28),(30,30)]
    h,w=sizes[index%len(sizes)];large=(h==30)
    bg=(seed+index+(1 if split=='test' else 0))%10
    palette=rng.sample([v for v in range(10) if v!=bg],6)
    keys=palette[:5] if large else palette[:4];unknown=palette[5]
    boxes=[[0,4,2*h//3+rng.choice([-1,0,1]),w//2+2+rng.choice([-1,0,1])],
           [h//3+rng.choice([-1,0,1]),w//3+2+rng.choice([-1,0,1]),h-1,w-1]]
    if large:boxes += [[2,w-8,h-5,w-3],[h-12,6,h-3,w//2],[1,w-6,2,w-5]]
    else:boxes += [[h-3,4,h-2,5]]
    if large:
        thin_row=rng.randrange(3,6);thin_col=w-10+rng.choice([-1,0,1])
        boxes[2]=[thin_row,4,thin_row+1,w-1]
        boxes[3]=[0,thin_col,h-1,thin_col+1]
    # All non-background glyphs are constructed before any legend/label access.
    g=[[bg]*w for _ in range(h)]
    occupied=set()
    for i,b in enumerate(boxes):
        solid=(i==len(boxes)-1)
        cells=[(r,c) for r in range(b[0],b[2]+1) for c in range(b[1],b[3]+1)] if solid else corners(b,rng.randrange(2))
        if occupied.intersection(cells):raise ValueError('Sampler corner collision')
        occupied.update(cells)
        for r,c in cells:g[r][c]=keys[i]
    # One unmapped block remains outside every rectangle; another must be erased
    # by the background-valued B rectangle. This teaches overwrite semantics.
    for r,c in [(0,0),(0,1),(1,0),(1,1),(h-4,w-4),(h-4,w-3),(h-3,w-4),(h-3,w-3)]:
        if (r,c) in occupied:raise ValueError('Unmapped block collided with a glyph')
        g[r][c]=unknown
    fills={key:rng.choice([v for v in range(10) if v!=key]) for key in keys}
    fills[keys[1]]=0
    if large:fills[keys[2]]=rng.choice([v for v in range(1,10) if v not in (bg,keys[2])])
    # Code zero decodes to background: A must differ from erasing layer B.
    fills[keys[0]]=rng.choice([v for v in range(1,10) if v not in (keys[0],bg)])
    order=keys[:];rng.shuffle(order)
    if split=='train' and index==0:order=sorted(keys,reverse=True)
    if split=='train' and index==1:order=sorted(keys)
    tr=rng.randrange(3,h-len(order)+1);tc=rng.randrange(2)
    for j,key in enumerate(order):g[tr+j][tc]=key;g[tr+j][tc+1]=fills[key]
    return g

def generate(seed,settings,demos=2,queries=4):
    priority=_setting(settings)
    for v,lo,hi,name in [(seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')]:
        if type(v) is not int or not lo<=v<=hi:raise ValueError(name+' out of range')
    train=[sample(seed,i,'train') for i in range(demos)];bank=[sample(seed,i,'test') for i in range(4)]
    _rng(seed,'private-query-presentation').shuffle(bank)
    pair=lambda grids:[{'input':g,'output':solve(g,priority)} for g in grids]
    return {'train':pair(train),'test':pair(bank[:queries]),'program_solution':program(settings)}
