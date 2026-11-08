"""Compose two pattern panels across a guide wall and isolated side marker."""
from __future__ import annotations
from collections import deque
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

PARAMETER='marker_panel'
VALUES=('second','third')
DEFAULT={PARAMETER:'second'}
DEMO_SIZES=(5,5,6,6,7,8)
QUERY_SIZES=(5,7,10,13)
RIVALS=('opposite_mode','identity','second_only','third_only','union_second_priority',
        'union_third_priority','wall_background','fixed_left_region','smaller_region_second',
        'larger_region_second','marker_cell_only')
D4=((-1,0),(1,0),(0,-1),(0,1))
D8=tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc)!=(0,0))


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if type(value) is not list or not 3<=len(value)<=30 or type(value[0]) is not list or not 3<=len(value[0])<=30:
        raise ValueError('Expected a rectangular grid between 3x3 and 30x30')
    if any(type(row) is not list or len(row)!=len(value[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value):
        raise ValueError('Expected rectangular exact integer colors 0..9')
    return deepcopy(value)


def parse_settings(value):
    if type(value) is not dict or set(value)!={PARAMETER} or type(value[PARAMETER]) is not str or value[PARAMETER] not in VALUES:
        raise ValueError(f'Expected exactly {PARAMETER} in {VALUES}')
    return value[PARAMETER]


def program(setting):
    mode=parse_settings(setting);text=Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
    anchor="(define marker-panel 'second)"
    if text.count(anchor)!=1:raise ValueError('Canonical marker-panel anchor changed')
    return text if mode=='second' else text.replace(anchor,"(define marker-panel 'third)")


def _components(cells,deltas):
    remaining=set(cells);answer=[]
    while remaining:
        start=min(remaining);remaining.remove(start);comp={start};q=deque([start])
        while q:
            r,c=q.popleft()
            for dr,dc in deltas:
                p=(r+dr,c+dc)
                if p in remaining:remaining.remove(p);comp.add(p);q.append(p)
        answer.append(comp)
    return answer


def panel_boxes(value):
    g=grid(value);h,w=len(g),len(g[0]);border=g[0][0]
    cells={(r,c) for r in range(h) for c in range(w) if g[r][c]!=border}
    comps=_components(cells,D4)
    boxes=[]
    for comp in comps:
        r0=min(r for r,c in comp);r1=max(r for r,c in comp);c0=min(c for r,c in comp);c1=max(c for r,c in comp)
        rect={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}
        if comp!=rect:raise ValueError('Each panel must be a solid non-border rectangle')
        boxes.append((r0,c0,r1-r0+1,c1-c0+1))
    boxes.sort()
    if len(boxes)!=4:raise ValueError('Expected exactly four separated panels')
    shape={(b[2],b[3]) for b in boxes}
    if len(shape)!=1:raise ValueError('Expected four equal panel rectangles')
    return boxes


def _extract(g,box):
    r0,c0,h,w=box;return [row[c0:c0+w] for row in g[r0:r0+h]]


def _guide_state(g):
    boxes=panel_boxes(g);panels=[_extract(g,b) for b in boxes];n,m=len(panels[0]),len(panels[0][0])
    p4=panels[3];bg=p4[0][0]
    if any(v!=bg for row in p4 for v in row):raise ValueError('Fourth input panel must be blank')
    guide={(r,c) for r in range(n) for c in range(m) if panels[0][r][c]!=bg}
    comps=sorted(_components(guide,D8),key=lambda x:(-len(x),min(x)))
    if len(comps)!=2 or len(comps[1])!=1 or len(comps[0])<2:raise ValueError('Guide must contain one wall and one isolated marker')
    wall=set(comps[0]);marker=next(iter(comps[1]))
    open_cells={(r,c) for r in range(n) for c in range(m) if (r,c) not in wall}
    regions=_components(open_cells,D4)
    marker_region=next((x for x in regions if marker in x),None)
    if marker_region is None or len(regions)<2:raise ValueError('Guide wall must separate the panel')
    return {'boxes':boxes,'panels':panels,'background':bg,'wall':wall,'marker':marker,
            'regions':regions,'marker_region':set(marker_region)}


def solve(value,mode='second',*,rival=None):
    g=grid(value)
    if type(mode) is not str or mode not in VALUES:raise ValueError('Unknown marker-panel mode')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    state=_guide_state(g);boxes=state['boxes'];p1,p2,p3,p4=state['panels'];bg=state['background']
    wall=state['wall'];region=state['marker_region'];regions=state['regions'];h,w=len(p1),len(p1[0])
    if rival=='identity':return g
    if rival=='opposite_mode':mode=VALUES[1-VALUES.index(mode)]
    marked,other=(p2,p3) if mode=='second' else (p3,p2)
    out=deepcopy(g);r0,c0,_,_=boxes[3]
    small=min(regions,key=len);large=max(regions,key=len)
    for r in range(h):
        for c in range(w):
            pos=(r,c);a=marked[r][c];b=other[r][c]
            if rival=='second_only':value=p2[r][c]
            elif rival=='third_only':value=p3[r][c]
            elif rival=='union_second_priority':value=p2[r][c] if p2[r][c]!=bg else p3[r][c]
            elif rival=='union_third_priority':value=p3[r][c] if p3[r][c]!=bg else p2[r][c]
            elif rival=='fixed_left_region':value=marked[r][c] if c<w//2 else other[r][c]
            elif rival=='smaller_region_second':value=p2[r][c] if pos in small else p3[r][c]
            elif rival=='larger_region_second':value=p2[r][c] if pos in large else p3[r][c]
            elif rival=='marker_cell_only':value=marked[r][c] if pos==state['marker'] else other[r][c]
            elif pos in wall:
                value=bg if rival=='wall_background' else (a if a!=bg else b)
            elif pos in region:value=a
            else:value=b
            out[r0+r][c0+c]=value
    return out


def input_errors(value):
    try:
        g=grid(value);state=_guide_state(g)
    except (ValueError,TypeError,IndexError,StopIteration) as error:return [str(error)]
    border=g[0][0]
    if any(v==border for b in state['boxes'] for row in _extract(g,b) for v in row):return ['Border color may not appear inside panels']
    if len(state['regions'])!=2:return ['Guide must make exactly two four-neighbor regions']
    return []


def _regions(n,wall):
    return _components({(r,c) for r in range(n) for c in range(n) if (r,c) not in wall},D4)


def _divider(n,kind,rng):
    if kind==0:
        c=rng.randint(1,n-2);return {(r,c) for r in range(n)}
    if kind==1:
        r=rng.randint(1,n-2);return {(r,c) for c in range(n)}
    if kind==2:return {(i,i) for i in range(n)}
    if kind==3:return {(i,n-1-i) for i in range(n)}
    if kind==4:
        c=rng.randint(1,n-3 if n>4 else n-2);r=rng.randint(1,n-2)
        return {(x,c) for x in range(r+1)}|{(r,y) for y in range(c,n)}
    c=rng.randint(2,n-2);r=rng.randint(1,n-2)
    return {(x,c) for x in range(r,n)}|{(r,y) for y in range(0,c+1)}


def pack_panels(panels,border,padding_to_30=False):
    if type(panels) is not list or len(panels)!=4:raise ValueError('Expected four panels')
    n=len(panels[0]);m=len(panels[0][0])
    if n!=m or any(len(p)!=n or any(len(row)!=m for row in p) for p in panels):raise ValueError('Expected equal square panels')
    if n<=6 and not padding_to_30:
        h=n+2;w=4*n+5;g=[[border]*w for _ in range(h)]
        boxes=[(1,1+i*(n+1),n,n) for i in range(4)]
    else:
        base=2*n+3;size=30 if padding_to_30 else base
        if size>30:raise ValueError('Packed grid exceeds 30x30')
        g=[[border]*size for _ in range(size)]
        boxes=[(1,1,n,n),(1,n+2,n,n),(n+2,1,n,n),(n+2,n+2,n,n)]
    for panel,(r0,c0,_,_) in zip(panels,boxes):
        for r in range(n):
            for c in range(n):g[r0+r][c0+c]=panel[r][c]
    return g


def sample(seed,stream,index,attempt=0):
    integer(seed,0,2**63-1,'seed');integer(attempt,0,4095,'attempt')
    if stream not in ('demo','query'):raise ValueError('Unknown stream')
    sizes=DEMO_SIZES if stream=='demo' else QUERY_SIZES;integer(index,0,len(sizes)-1,'index')
    n=sizes[index];rng=random.Random(f'divider-compose-v2:{seed}:{stream}:{index}:{attempt}')
    border,bg,guide_color,p2color,p3color=rng.sample(range(10),5)
    wall=_divider(n,(index+attempt)%6,rng);regions=_regions(n,wall)
    if len(regions)!=2:raise ValueError('Divider did not make exactly two regions')
    candidates=[]
    for region in regions:
        safe=[p for p in region if all((p[0]+dr,p[1]+dc) not in wall for dr,dc in D8)]
        if safe:candidates.append((region,safe))
    if not candidates:raise ValueError('No isolated marker position')
    marker_region,safe=rng.choice(candidates);marker=rng.choice(sorted(safe))
    p1=[[bg]*n for _ in range(n)]
    for r,c in wall|{marker}:p1[r][c]=guide_color
    p2=[[bg]*n for _ in range(n)];p3=[[bg]*n for _ in range(n)]
    other_region=next(x for x in regions if x is not marker_region)
    def choose(region,k):
        cells=sorted(region);return rng.sample(cells,min(k,len(cells)))
    density=max(2,n//2)
    for r,c in choose(marker_region,density)+choose(other_region,density):p2[r][c]=p2color
    for r,c in choose(marker_region,density)+choose(other_region,density):p3[r][c]=p3color
    extra=max(1,n*n//8)
    for r,c in rng.sample([(r,c) for r in range(n) for c in range(n)],extra):p2[r][c]=p2color
    for r,c in rng.sample([(r,c) for r in range(n) for c in range(n)],extra):p3[r][c]=p3color
    wcells=sorted(wall)
    both=wcells[len(wcells)//2];p2[both[0]][both[1]]=p2color;p3[both[0]][both[1]]=p3color
    if len(wcells)>2:
        a,b=wcells[0],wcells[-1];p2[a[0]][a[1]]=p2color;p3[a[0]][a[1]]=bg
        p3[b[0]][b[1]]=p3color;p2[b[0]][b[1]]=bg
    p4=[[bg]*n for _ in range(n)]
    g=pack_panels([p1,p2,p3,p4],border,padding_to_30=(stream=='query' and index==3))
    errors=input_errors(g)
    if errors:raise ValueError('; '.join(errors))
    if solve(g,'second')==solve(g,'third'):raise ValueError('Settings did not diverge')
    return g


@lru_cache(maxsize=64)
def teaching(seed):
    for attempt in range(256):
        try:grids=[sample(seed,'demo',i,attempt) for i in range(2)]
        except ValueError:continue
        if all(survivors([{'input':g,'output':solve(g,mode)} for g in grids],{PARAMETER:mode})==['intended'] for mode in VALUES):
            return tuple(tuple(tuple(row) for row in g) for g in grids)
    raise ValueError('Bounded teaching search could not refute declared rivals')


def generate(seed,settings,demos,queries):
    integer(seed,0,2**63-1,'seed');mode=parse_settings(settings)
    integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    first=[list(map(list,g)) for g in teaching(seed)]
    inputs=first+[sample(seed,'demo',i) for i in range(2,demos)]
    tests=[sample(seed,'query',i) for i in range(queries)]
    pairs=lambda xs:[{'input':g,'output':solve(g,mode)} for g in xs]
    return {'train':pairs(inputs),'test':pairs(tests),'program_solution':program(settings)}


def survivors(train,setting):
    mode=parse_settings(setting);result=['intended']
    for name in RIVALS:
        if all(solve(p['input'],mode,rival=name)==p['output'] for p in train):result.append(name)
    return result


def public_view(episode,query_index):
    integer(query_index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
            'test':[{'input':grid(episode['test'][query_index]['input'])}]}


def presentation_order(seed):
    integer(seed,0,2**63-1,'presentation seed');order=list(range(4));random.Random(f'divider-presentation-v1:{seed}').shuffle(order);return order


def public_turns(seed,setting,demos,presentation_seed=0,count=4):
    integer(count,1,4,'presentation count');integer(presentation_seed,0,2**63-1,'presentation seed')
    episode=generate(seed,setting,demos,4);order=presentation_order(seed^presentation_seed)
    return [public_view(episode,i) for i in order[:count]]
