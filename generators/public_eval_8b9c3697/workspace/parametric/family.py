"""General comb-socket docking with an episode-fixed candidate distance order.

All geometry is inferred from the input. The shorter middle tooth defines a
lane's perpendicular width and stopping tip; candidates must be solid red
rectangles exactly aligned with that lane. No official data are read here.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib
import json
import random

HERE=Path(__file__).resolve().parent
SETTINGS=('nearest','farthest')
DIRECTIONS=((1,0),(-1,0),(0,1),(0,-1))
COUNTERFACTUAL_FILE='counterfactual-long-tooth.rkt'


def strict_grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
        or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected a rectangular 1..30 grid of exact integer colors 0..9')
    return [row[:] for row in grid]


def components(grid,background):
    seen=set();result=[]
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color==background or (r,c) in seen:continue
            todo=[(r,c)];seen.add((r,c));cells=[]
            while todo:
                a,b=todo.pop();cells.append((a,b))
                for dr,dc in DIRECTIONS:
                    q=(a+dr,b+dc)
                    if 0<=q[0]<len(grid) and 0<=q[1]<len(row) and q not in seen and grid[q[0]][q[1]]==color:
                        seen.add(q);todo.append(q)
            result.append({'color':color,'cells':sorted(cells)})
    return result


def bounds(cells,direction):
    dr,dc=direction;er,ec=-dc,dr
    ts=[r*dr+c*dc for r,c in cells];us=[r*er+c*ec for r,c in cells]
    return min(ts),max(ts),min(us),max(us)


def socket_profile(obj,direction):
    """Recognize three contiguous prong groups with a uniquely shorter middle."""
    dr,dc=direction;er,ec=-dc,dr;cells=set(obj['cells'])
    t0,t1,u0,u1=bounds(cells,direction)
    if t1-t0<2 or u1-u0<4:return None
    heights=[sum(r*er+c*ec==u for r,c in cells) for u in range(u0,u1+1)]
    if min(heights)!=1:return None
    for i,height in enumerate(heights):
        u=u0+i
        if any((dr*t+er*u,dc*t+ec*u) not in cells for t in range(t0,t0+height)):
            return None
    groups=[]
    for i,height in enumerate(heights):
        if height>1:
            if not groups or i!=groups[-1][-1]+1:groups.append([])
            groups[-1].append(i)
    if len(groups)!=3:return None
    tooth_heights=[]
    for group in groups:
        values={heights[i] for i in group}
        if len(values)!=1:return None
        tooth_heights.append(next(iter(values)))
    if not tooth_heights[0]==tooth_heights[2]>tooth_heights[1]>1:return None
    mid=groups[1]
    return {'direction':direction,'across':(er,ec),'u0':u0+mid[0],'u1':u0+mid[-1],
            'tip':t0+tooth_heights[1]-1,'long_tip':t0+tooth_heights[0]-1,
            'spine':t0,'color':obj['color'],'cells':obj['cells']}


def rectangular(obj):
    rs=[r for r,c in obj['cells']];cs=[c for r,c in obj['cells']]
    return len(obj['cells'])==(max(rs)-min(rs)+1)*(max(cs)-min(cs)+1)


def compatible(obj,socket):
    lo,hi,u0,u1=bounds(obj['cells'],socket['direction'])
    return rectangular(obj) and (u0,u1)==(socket['u0'],socket['u1']) and lo>socket['tip']


def overlaps_lane(obj,socket):
    lo,hi,u0,u1=bounds(obj['cells'],socket['direction'])
    return rectangular(obj) and lo>socket['tip'] and max(u0,socket['u0'])<=min(u1,socket['u1'])


def analyze(grid):
    grid=strict_grid(grid);freq=Counter(v for row in grid for v in row)
    background=max(freq,key=lambda v:freq[v])
    if background in (0,2):raise ValueError('Admitted background is nonzero and nonred')
    objects=components(grid,background);reds=[o for o in objects if o['color']==2];sockets=[]
    for obj in objects:
        if obj['color']==2:continue
        possible=[p for d in DIRECTIONS if (p:=socket_profile(obj,d)) is not None]
        if len(possible)>1:raise ValueError('Ambiguous comb orientation')
        if possible:
            socket=possible[0]
            socket['candidates']=sorted([o for o in reds if compatible(o,socket)],
                                        key=lambda o:bounds(o['cells'],socket['direction'])[0])
            sockets.append(socket)
    if not sockets:raise ValueError('No valid comb socket')
    # Streams in the admitted grammar may not compete for the same red block.
    candidates=[tuple(o['cells']) for s in sockets for o in s['candidates']]
    if len(candidates)!=len(set(candidates)):raise ValueError('One red object is eligible for multiple sockets')
    return {'background':background,'sockets':sockets,'reds':reds,'grid':grid}


def _draw(info,order,variant=None):
    bg=info['background'];grid=info['grid']
    out=[[bg if v==2 else v for v in row] for row in grid]
    sockets=info['sockets'][:1] if variant=='first_socket_only' else info['sockets']
    if variant=='down_only':sockets=[s for s in sockets if s['direction']==(1,0)]
    for socket in sockets:
        candidates=socket['candidates']
        if variant=='ignore_width':
            candidates=sorted([o for o in info['reds'] if overlaps_lane(o,socket)],key=lambda o:bounds(o['cells'],socket['direction'])[0])
        if not candidates:continue
        if variant=='largest_red':obj=max(candidates,key=lambda o:len(o['cells']))
        elif variant=='smallest_red':obj=min(candidates,key=lambda o:len(o['cells']))
        else:obj=candidates[0 if order=='nearest' else -1]
        lo,hi,u0,u1=bounds(obj['cells'],socket['direction']);depth=hi-lo+1
        tip=socket['long_tip'] if variant=='long_tooth_stop' else socket['tip']
        dr,dc=socket['direction'];er,ec=socket['across']
        def paint(t,u,color):
            r,c=dr*t+er*u,dc*t+ec*u
            if 0<=r<len(out) and 0<=c<len(out[0]):out[r][c]=color
        if variant!='no_trail':
            for t in range(tip+1,hi+1):
                for u in range(u0,u1+1):paint(t,u,0)
        for t in range(tip+1,tip+1+depth):
            for u in range(u0,u1+1):paint(t,u,2)
    if variant=='keep_distractors':
        for r,row in enumerate(grid):
            for c,value in enumerate(row):
                if value==2 and out[r][c]==bg:out[r][c]=2
    return out


def solve(grid,order='nearest'):
    if order not in SETTINGS:raise ValueError('Unknown candidate distance order')
    return _draw(analyze(grid),order)


def program(settings):
    if type(settings) is not dict or set(settings)!={'candidate_order'} or settings['candidate_order'] not in SETTINGS:
        raise ValueError('Expected exactly one declared candidate_order')
    path=HERE.parents[1]/'reference.rkt' if settings['candidate_order']=='nearest' else HERE/'farthest.rkt'
    return path.read_text(encoding='utf-8')


def _rng(seed,domain):
    return random.Random(int.from_bytes(hashlib.sha256(f'sockets-v1:{seed}:{domain}'.encode()).digest(),'big'))


def _turn(grid,rotation,reflection=False):
    out=[row[::-1] if reflection else row[:] for row in grid]
    for _ in range(rotation%4):out=[list(row) for row in zip(*out[::-1])]
    return out


def scene(seed,domain,count=2,depth_pattern=0):
    """Noninterfering socket panels, independently oriented and colored.

    Each has two exact-width candidates and mismatched-width objects closer
    and farther than those candidates. Teaching depths reverse size proxies.
    """
    if count not in (2,3,4):raise ValueError('Socket count must be 2,3,4')
    rng=_rng(seed,domain);bg=rng.choice([1,3,4,5,6,7,8,9])
    palette=[c for c in range(1,10) if c not in (2,bg)]
    panel_size=14
    if count==2:height,width=14,29;anchors=[(0,0),(0,15)]
    else:height=width=30;anchors=[(0,0),(0,16),(16,0),(16,16)];rng.shuffle(anchors);anchors=anchors[:count]
    out=[[bg]*width for _ in range(height)]
    if count==2:
        orientations=list(rng.choice(((1,3),(0,2),(2,0),(1,0),(2,3),(0,3),(1,2))))
    else:
        # Rays point away from the other quadrants. A blank panel boundary is
        # NOT a wall: arbitrary orientations would capture foreign red blocks.
        allowed={(0,0):(1,2),(0,16):(2,3),(16,0):(0,1),(16,16):(0,3)}
        orientations=[rng.choice(allowed[a]) for a in anchors]
    for index,(ar,ac) in enumerate(anchors):
        g=[[bg]*panel_size for _ in range(panel_size)]
        q=1+(index+rng.randrange(3))%3;color=rng.choice(palette)
        spine_width=q+6;left=rng.randrange(panel_size-spine_width+1)
        top=rng.randrange(2);short=rng.choice((1,2));long=rng.choice((3,4))
        # Keep the complete short-tooth lane away from lateral boundaries.
        for c in range(left,left+spine_width):g[top][c]=color
        for r in range(top+1,top+long+1):
            g[r][left+1]=color;g[r][left+q+4]=color
        mid=left+3
        for r in range(top+1,top+short+1):
            for c in range(mid,mid+q):g[r][c]=color
        near_depth,far_depth=((2,1) if depth_pattern%2==0 else (1,2))
        if depth_pattern>=2:
            near_depth=rng.choice((1,2));far_depth=rng.choice((1,2))
        for start,depth in ((6,near_depth),(10,far_depth)):
            for r in range(start,start+depth):
                for c in range(mid,mid+q):g[r][c]=2
        # Width q+1 cannot be mistaken for a compatible payload. Its axial
        # position would win the nearest/farthest rule if width were ignored.
        for r in (4,13):
            for c in range(mid,mid+q+1):
                if g[r][c]!=bg:raise AssertionError('Constructive socket/payload collision')
                g[r][c]=2
        # A short off-lane red distractor remains separate from all payloads.
        off_col=0 if mid>1 else 13
        g[8][off_col]=2
        g=_turn(g,orientations[index],bool(rng.randrange(2)))
        for r,row in enumerate(g):
            for c,value in enumerate(row):out[ar+r][ac+c]=value
    return _turn(out,rng.randrange(4),bool(rng.randrange(2)))


def generate(seed,settings,demos,queries):
    text=program(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('Expected a nonnegative 63-bit seed')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or queries!=4:raise ValueError('Exactly four private queries are required')
    train=[scene(seed,f'demo:{i}',2+i%3,i%2) for i in range(demos)]
    bank=[scene(seed,f'query:{i}',(2,4,3,4)[i],2+i) for i in range(4)]
    _rng(seed,'presentation').shuffle(bank)
    label=lambda g:{'input':g,'output':solve(g,settings['candidate_order'])}
    return {'train':list(map(label,train)),'test':list(map(label,bank)),'program_solution':text}


def rival_names(order):
    return ['opposite_setting','no_trail','keep_distractors','ignore_width','long_tooth_stop',
            'largest_red','smallest_red','first_socket_only','down_only','identity']


def rival(grid,order,name):
    if name=='identity':return strict_grid(grid)
    if name=='opposite_setting':return solve(grid,SETTINGS[order=='nearest'])
    if name not in rival_names(order):raise ValueError('Unknown rival')
    return _draw(analyze(grid),order,name)


def surviving_rivals(episode):
    order=next(v for v in SETTINGS if program({'candidate_order':v})==episode['program_solution'])
    return [name for name in rival_names(order) if all(rival(p['input'],order,name)==p['output'] for p in episode['train'])]


def public_view(episode,query_index=0):
    if type(query_index) is not int or not 0<=query_index<len(episode['test']):raise ValueError('Invalid query index')
    visible={'train':[{'input':strict_grid(p['input']),'output':strict_grid(p['output'])} for p in episode['train']],
             'test':[{'input':strict_grid(episode['test'][query_index]['input'])}]}
    return (json.dumps(visible,sort_keys=True,separators=(',',':'))+'\n').encode()


def dependency():
    return {'step_a':'Infer each comb orientation and derive the shorter middle tooth\'s tip and exact perpendicular width from its cell geometry.',
            'intermediate':'Oriented socket lanes: direction vectors, exact transverse intervals, short-tooth tip coordinates and aligned red-rectangle candidates ordered by distance.',
            'step_b':'Choose the nearest or farthest compatible payload, erase distractors, dock against the derived tip and paint exactly its swept trail black.',
            'why_b_depends_on_a':'Neither eligible payloads nor their final positions are known before extracting the middle tooth. Replacing its tip with the long guard tip preserves candidate identity but changes docking and trail cells.'}


def causal_value(grid):
    info=analyze(grid)
    return {'background':info['background'],'lanes':[
        {'direction':list(s['direction']),'across':list(s['across']),'width':s['u1']-s['u0']+1,
         'correct_short_tip':s['tip'],'wrong_long_tip':s['long_tip'],
         'candidate_projected_bounds':[list(bounds(o['cells'],s['direction'])) for o in s['candidates']]}
        for s in info['sockets']]}
