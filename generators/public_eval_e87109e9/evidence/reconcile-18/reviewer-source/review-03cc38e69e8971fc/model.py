"""Header-programmed cyan cursor routes with target turns and blocker bounces."""
from __future__ import annotations
from collections import Counter
import copy
import random

GENERATOR_ID=TASK_ID='public_eval_e87109e9'
RULE_TASK_ID='ee_e87109e9'
VERSION='1.0.0'
SUMMARY='Decode a four-slot header and paint cursor excursions with target turns and farther-extension bounces.'
AXES={'turn_mode':['header','reverse']}
INVARIANTS=['four header commands','cyan square cursor','modal body background','axis-aligned rectangular targets and blockers']
D4=((-1,0),(0,1),(1,0),(0,-1))


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def validate_grid(grid):
    if type(grid) is not list or not 7<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('grid must be a 7..30 by 1..30 rectangle')
    width=len(grid[0])
    if any(type(row) is not list or len(row)!=width or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('grid must contain exact integer colors 0..9')
    return grid


def _components(grid,accepted):
    h,w=len(grid),len(grid[0]);seen=set();result=[]
    for r in range(h):
        for c in range(w):
            if (r,c) in seen or not accepted(grid[r][c]):continue
            color=grid[r][c];stack=[(r,c)];seen.add((r,c));cells=[]
            while stack:
                a,b=stack.pop();cells.append((a,b))
                for dr,dc in D4:
                    rr,cc=a+dr,b+dc
                    if 0<=rr<h and 0<=cc<w and (rr,cc) not in seen and accepted(grid[rr][cc]) and grid[rr][cc]==color:
                        seen.add((rr,cc));stack.append((rr,cc))
            result.append({'color':color,'cells':tuple(sorted(cells)),'bbox':_bbox(cells)})
    return result


def _bbox(cells):
    return (min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells))


def _header(grid):
    frame=grid[0][0];width=len(grid[0])
    ends=[r for r in range(1,len(grid)) if all(v==frame for v in grid[r])]
    if not ends:raise ValueError('header closing row missing')
    end=ends[0]
    if end<2:raise ValueError('header is too short')
    nonframe=[c for c in range(width) if any(grid[r][c]!=frame for r in range(end+1))]
    runs=[]
    for c in nonframe:
        if not runs or c!=runs[-1][-1]+1:runs.append([c])
        else:runs[-1].append(c)
    if len(runs)!=4:raise ValueError('exactly four header slots required')
    commands=[]
    for run in runs:
        colors=[grid[r][c] for r in range(1,end) for c in run if grid[r][c] not in (frame,0)]
        if not colors:raise ValueError('header slot lacks a target stripe')
        target=Counter(colors).most_common(1)[0][0]
        cols=[c for c in run if any(grid[r][c]==target for r in range(1,end))]
        hand='left' if sum(cols)/len(cols)<(run[0]+run[-1])/2 else 'right'
        commands.append({'target':target,'hand':hand,'columns':(run[0],run[-1])})
    return {'frame':frame,'end':end,'commands':commands,'body':[row[:] for row in grid[end+1:]]}


def _turn(direction,hand):
    dr,dc=direction
    return (-dc,dr) if hand=='left' else (dc,-dr)


def _block_cells(r,c,size):
    return {(rr,cc) for rr in range(r,r+size) for cc in range(c,c+size)}


def _route(data,command,turn_mode):
    h,w=data['shape'];size=data['cursor']['size'];home=(data['cursor']['r'],data['cursor']['c'])
    occupied=data['_occupied'];owners=data['_owners'];objects=data['objects']
    target=command['target'];hand=command['hand']
    if turn_mode=='reverse':hand='right' if hand=='left' else 'left'

    def inbounds(r,c):return 0<=r and 0<=c and r+size<=h and c+size<=w
    def hit_at(r,c):return _block_cells(r,c,size)&occupied
    aligned=[]
    for name,d in (('up',(-1,0)),('right',(0,1)),('down',(1,0)),('left',(0,-1))):
        r,c=home;steps=0
        while inbounds(r+d[0],c+d[1]):
            nr,nc=r+d[0],c+d[1];hit=hit_at(nr,nc)
            if hit:
                if any(objects[owners[p]]['color']==target for p in hit):aligned.append((steps+1,name,d))
                break
            r,c=nr,nc;steps+=1
    positions=[home];bounces=[]
    if not aligned:
        r,c=home
        while inbounds(r-1,c):r-=1;positions.append((r,c))
        return {'target':target,'hand':hand,'aligned':False,'initial_direction':'up','positions':positions,'bounces':bounces}

    _,name,d=min(aligned,key=lambda x:x[0]);r,c=home
    while True:
        nr,nc=r+d[0],c+d[1]
        if not inbounds(nr,nc) or hit_at(nr,nc):break
        r,c=nr,nc;positions.append((r,c))
    d=_turn(d,hand);seen=set()
    while True:
        state=(r,c,d)
        if state in seen:break
        seen.add(state)
        nr,nc=r+d[0],c+d[1]
        if not inbounds(nr,nc):break
        hit=hit_at(nr,nc)
        if not hit:
            r,c=nr,nc;positions.append((r,c));continue
        ids=Counter(owners[p] for p in hit);obj=objects[ids.most_common(1)[0][0]]
        r0,c0,r1,c1=obj['bbox']
        if d[0]:
            left=c-c0;right=c1-(c+size-1);nd=(0,-1) if left>right else (0,1)
        else:
            up=r-r0;down=r1-(r+size-1);nd=(-1,0) if up>down else (1,0)
        bounces.append({'at':(r,c),'blocker':obj['color'],'from':d,'to':nd,'bbox':obj['bbox']})
        d=nd
    return {'target':target,'hand':hand,'aligned':True,'initial_direction':name,'positions':positions,'bounces':bounces}


def analyze(grid,turn_mode='header'):
    validate_grid(grid)
    if turn_mode not in ('header','reverse'):raise ValueError('turn_mode must be header or reverse')
    parsed=_header(grid);body=parsed['body'];h,w=len(body),len(body[0])
    bg=Counter(v for row in body for v in row).most_common(1)[0][0]
    cursor_cells=[(r,c) for r,row in enumerate(body) for c,v in enumerate(row) if v==8]
    if not cursor_cells:raise ValueError('cyan cursor missing')
    r0,c0,r1,c1=_bbox(cursor_cells);size=r1-r0+1
    if c1-c0+1!=size or len(cursor_cells)!=size*size:raise ValueError('cyan cursor must be a solid square')
    objects=_components(body,lambda v:v not in (bg,8));owners={}
    for i,obj in enumerate(objects):
        for p in obj['cells']:owners[p]=i
    data={'header_end':parsed['end'],'commands':copy.deepcopy(parsed['commands']),'body':body,'background':bg,
          'shape':(h,w),'cursor':{'r':r0,'c':c0,'size':size,'cells':tuple(cursor_cells)},
          'objects':objects,'_owners':owners,'_occupied':set(owners)}
    data['route_summary']=[_route(data,command,turn_mode) for command in data['commands']]
    return data


def solve(grid,turn_mode='header'):
    data=analyze(grid,turn_mode);out=[row[:] for row in data['body']];n=data['cursor']['size']
    for route in data['route_summary']:
        for r,c in route['positions']:
            for rr in range(r,r+n):
                for cc in range(c,c+n):out[rr][cc]=8
    return out


_LAYOUTS=(
 {'h':19,'cursor':(7,8,2),'rects':((0,(3,0,11,3)),(2,(4,18,10,21)),(3,(16,4,18,14)))},
 {'h':19,'cursor':(8,8,2),'rects':((0,(5,0,11,3)),(1,(16,5,18,12)),(2,(0,13,1,17)),(3,(5,16,10,19)))},
 {'h':19,'cursor':(11,12,2),'rects':((0,(16,8,18,21)),(1,(3,20,13,23)),(2,(0,8,3,17)),(3,(7,0,18,2)))},
 {'h':24,'cursor':(7,8,3),'rects':((0,(6,0,14,2)),(1,(0,21,12,23)),(2,(17,7,19,15)),(3,(20,17,23,20)))},
)


def _paint_rect(grid,box,color):
    r0,c0,r1,c1=box
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):grid[r][c]=color


def _make_header(commands):
    frame=5;grid=[[frame]*24 for _ in range(6)]
    for r in range(1,5):
        for slot,(color,hand) in enumerate(commands):
            base=slot*6
            for c in range(base+1,base+5):grid[r][c]=0
            grid[r][base+1 if hand=='left' else base+4]=color
    return grid


def scene(seed,index,*,query=False):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng=random.Random(f'cursor-route-v1|{seed}|{index}|{query}')
    layout=copy.deepcopy(_LAYOUTS[index%len(_LAYOUTS)])
    available=[1,2,3,4,6,7,9]
    rng.shuffle(available);targets=available[:4];bg=available[4]
    if index%len(_LAYOUTS) in (0,3):
        # One deliberately absent command preserves the parent's fallback branch.
        absent=1 if index%len(_LAYOUTS)==0 else 3
    else:absent=None
    hands=[rng.choice(('left','right')) for _ in range(4)]
    # Make every minimum lesson setting-distinguishing and keep a stable stress bounce.
    hands[0]='left' if (seed+index)%2==0 else 'right'
    body=[[bg]*24 for _ in range(layout['h'])]
    for label,box in layout['rects']:
        if label!=absent:_paint_rect(body,box,targets[label])
    cr,cc,n=layout['cursor'];_paint_rect(body,(cr,cc,cr+n-1,cc+n-1),8)
    if (seed+index)%2:
        body=[row[::-1] for row in body]
        cc=24-cc-n
    commands=[(targets[i],hands[i]) for i in range(4)]
    grid=_make_header(commands)+body
    if self_check(grid):
        raise AssertionError('invalid generated cursor scene: '+','.join(self_check(grid)))
    return grid


def generate(seed,sample_index,difficulty=None):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    return scene(seed,sample_index,query=False)


def self_check(grid):
    errors=[]
    try:
        data=analyze(grid)
        if len(data['commands'])!=4:errors.append('wrong command count')
        if data['cursor']['size'] not in (2,3):errors.append('unsupported cursor size')
        if len(solve(grid))!=data['shape'][0]:errors.append('output height mismatch')
        if len({(c['target'],c['hand']) for c in data['commands']})<3:errors.append('degenerate command header')
    except Exception as exc:errors.append(str(exc))
    return errors


def policy_outputs(grid):
    normal=solve(grid,'header');reverse=solve(grid,'reverse');body=_header(grid)['body']
    no_turn=[row[:] for row in body]
    return {'header':normal,'reverse':reverse,'identity_body':body,'no_trails':no_turn}
