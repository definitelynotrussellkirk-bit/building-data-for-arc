"""Diagonal signal segments with episode-fixed red branch orientation.

The sampler is independent of the selected setting. The first two immutable
teaching inputs contain both source diagonal orientations, multiple active red
triggers, inactive red distractors, finite blue segments, and isolated blue
controls. All labels are deterministic Python claims; protected Racket replays
remain the source-bound verification authority.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import collections
import random

PARAMETER='beam_reach'
VALUES=('both_edges','forward_edge')
DEFAULT={PARAMETER:VALUES[0]}
DEMO_DIMS=((10,12),(11,13),(13,15),(15,17),(18,20),(21,24))
QUERY_DIMS=((12,15),(18,21),(24,27),(30,30))
BACKGROUNDS=(0,2,3,4,5,7,8,9)
RIVALS=('opposite_reach','connect_only','all_reds','no_connect','infinite_signal',
        'beam_color_blue','first_trigger_only','last_trigger_only',
        'always_positive_diagonal','always_negative_diagonal','reverse_edge','identity')


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list or not 1<=len(value[0])<=30:
        raise ValueError('Expected a nonempty grid of at most 30x30')
    if any(type(row) is not list or len(row)!=len(value[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value):
        raise ValueError('Expected rectangular exact integer colors 0..9')
    return deepcopy(value)


def settings(value):
    if type(value) is not dict or set(value)!={PARAMETER} or type(value[PARAMETER]) is not str or value[PARAMETER] not in VALUES:
        raise ValueError(f'Expected exactly {PARAMETER} in {VALUES}')
    return value[PARAMETER]


def program(setting):
    reach=settings(setting)
    text=Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
    anchor="(define beam-reach 'both_edges)"
    if text.count(anchor)!=1:raise ValueError('Canonical beam-reach anchor changed')
    return text if reach=='both_edges' else text.replace(anchor,"(define beam-reach 'forward_edge)")


def _background(g):
    counts=collections.Counter(v for row in g for v in row)
    highest=max(counts.values());winners=[v for v,n in counts.items() if n==highest]
    if len(winners)!=1:raise ValueError('Expected a unique modal background')
    return winners[0]


def _between(p,q):
    dr=q[0]-p[0];dc=q[1]-p[1]
    if dr==0 or abs(dr)!=abs(dc):return None
    sr=1 if dr>0 else -1;sc=1 if dc>0 else -1
    return {'endpoints':[list(p),list(q)],'row_step':sr,'col_step':sc,
            'cells':[[p[0]+k*sr,p[1]+k*sc] for k in range(abs(dr)+1)]}


def derive(value):
    g=grid(value);background=_background(g);h,w=len(g),len(g[0])
    blue=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==1]
    red=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==6]
    segments=[]
    for i,p in enumerate(blue):
        for q in blue[i+1:]:
            segment=_between(p,q)
            if segment is not None:segments.append(segment)
    if not segments:raise ValueError('Expected at least one diagonal blue endpoint pair')
    triggers=[]
    for p in red:
        memberships=[i for i,s in enumerate(segments) if list(p) in s['cells']]
        if memberships:triggers.append({'cell':list(p),'segments':memberships})
    return {'background':background,'height':h,'width':w,'blue':[list(p) for p in blue],
            'red':[list(p) for p in red],'segments':segments,'triggers':triggers,
            'inactive_red':[list(p) for p in red if all(list(p)!=t['cell'] for t in triggers)]}


def _line(h,w,p,dr,dc):
    return [[r,c] for r in range(h) for c in range(w)
            if (r-p[0])*dc==(c-p[1])*dr]


def _beam(h,w,p,dr,dc,reach):
    cells=_line(h,w,p,dr,dc)
    if reach=='both_edges':return cells
    return [[r,c] for r,c in cells if (r-p[0])*dr+(c-p[1])*dc>=0]


def solve(value,reach='both_edges',*,rival=None):
    g=grid(value)
    if type(reach) is not str or reach not in VALUES:raise ValueError('Unknown beam reach')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    state=derive(g);out=deepcopy(g);bg=state['background'];h=state['height'];w=state['width']
    if rival=='identity':return out
    if rival=='opposite_reach':reach='forward_edge' if reach=='both_edges' else 'both_edges'
    connect=rival not in ('no_connect',)
    if connect:
        cells=[]
        for segment in state['segments']:
            if rival=='infinite_signal':
                cells.extend(_line(h,w,segment['cells'][0],segment['row_step'],segment['col_step']))
            else:cells.extend(segment['cells'])
        for r,c in cells:
            if out[r][c]==bg:out[r][c]=1
    if rival=='connect_only':return out
    associations=[]
    for trigger in state['triggers']:
        for index in trigger['segments']:associations.append((trigger['cell'],state['segments'][index]))
    if rival=='all_reds':
        first=state['segments'][0];known={tuple(p) for p,_ in associations}
        associations.extend((p,first) for p in state['red'] if tuple(p) not in known)
    if rival=='first_trigger_only':associations=associations[:1]
    if rival=='last_trigger_only':associations=associations[-1:]
    color=1 if rival=='beam_color_blue' else 6
    for p,segment in associations:
        if rival=='always_positive_diagonal':dr,dc=1,1
        elif rival=='always_negative_diagonal':dr,dc=1,-1
        else:dr,dc=segment['row_step'],-segment['col_step']
        current_reach=reach
        if rival=='reverse_edge':dr,dc=-dr,-dc;current_reach='forward_edge'
        for r,c in _beam(h,w,p,dr,dc,current_reach):out[r][c]=color
    return out


def _rng(seed,role,index,attempt):
    return random.Random(f'db695cfb-diagonal-v1:{seed}:{role}:{index}:{attempt}')


def _add_isolated_blue(g,rng,count,existing):
    h,w=len(g),len(g[0]);points=list(existing)
    candidates=[(r,c) for r in range(h) for c in range(w) if g[r][c] not in (1,6)]
    rng.shuffle(candidates)
    for p in candidates:
        if all(abs(p[0]-q[0])!=abs(p[1]-q[1]) for q in points):
            g[p[0]][p[1]]=1;points.append(p)
            if len(points)==len(existing)+count:return
    raise ValueError('Could not place isolated blue controls')


def _scene(seed,role,index,attempt):
    dims=QUERY_DIMS[index] if role=='query' else DEMO_DIMS[index%len(DEMO_DIMS)]
    h,w=dims;rng=_rng(seed,role,index,attempt);bg=rng.choice(BACKGROUNDS);g=[[bg]*w for _ in range(h)]
    orientation=1 if index%2==0 else -1
    max_len=min(h,w)-4
    if max_len<5:raise ValueError('Profile too small')
    length=rng.randint(max(5,max_len-3),max_len)
    r0=rng.randint(1,h-length-2)
    if orientation==1:
        c0=rng.randint(1,w-length-2);p=(r0,c0);q=(r0+length,c0+length)
    else:
        c0=rng.randint(1,w-length-2);p=(r0,c0+length);q=(r0+length,c0)
    g[p[0]][p[1]]=1;g[q[0]][q[1]]=1
    isolated=3 if (role=='query' and index==3) else 1
    _add_isolated_blue(g,rng,isolated,[p,q])
    state=derive(g)
    if len(state['segments'])!=1:raise ValueError('Unexpected extra signal segment')
    segment=[tuple(x) for x in state['segments'][0]['cells']]
    internal=segment[1:-1];rng.shuffle(internal)
    trigger_count=min(len(internal),5 if (role=='query' and index==3) else 2)
    if trigger_count<2:raise ValueError('Not enough trigger sites')
    chosen=[]
    for cell in internal:
        if all(abs(cell[0]-q0[0])>=2 for q0 in chosen):chosen.append(cell)
        if len(chosen)==trigger_count:break
    if len(chosen)<trigger_count:chosen=internal[:trigger_count]
    for r,c in chosen:g[r][c]=6
    decoys=14 if (role=='query' and index==3) else 3
    candidates=[(r,c) for r in range(h) for c in range(w) if g[r][c]==bg and (r,c) not in segment]
    rng.shuffle(candidates)
    for r,c in candidates[:decoys]:g[r][c]=6
    state=derive(g)
    if len(state['segments'])!=1 or len(state['triggers'])!=trigger_count or len(state['inactive_red'])<1:
        raise ValueError('Scene grammar drift')
    if solve(g,'both_edges')==solve(g,'forward_edge'):raise ValueError('Settings alias')
    return g


def _raw_scene(seed,role,index):
    for attempt in range(256):
        try:return _scene(seed,role,index,attempt)
        except ValueError:pass
    raise ValueError('Bounded scene search exhausted')


@lru_cache(maxsize=512)
def teaching(seed):
    integer(seed,0,2**63-1,'seed')
    for attempt in range(256):
        try:pair=(_scene(seed,'teach',0,attempt),_scene(seed,'teach',1,attempt))
        except ValueError:continue
        if all(survivors([{'input':deepcopy(g),'output':solve(g,value)} for g in pair],{PARAMETER:value})==['intended'] for value in VALUES):
            return deepcopy(pair)
    raise ValueError('Bounded teaching search could not refute declared rivals')


def sample(seed,role,index):
    integer(seed,0,2**63-1,'seed')
    if role not in ('demo','query'):raise ValueError('role must be demo or query')
    integer(index,0,5 if role=='demo' else 3,'index')
    if role=='demo' and index<2:return deepcopy(teaching(seed)[index])
    return _raw_scene(seed,role,index)


def generate(seed,setting,demos,queries):
    integer(seed,0,2**63-1,'seed');turn=settings(setting)
    integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    demo_inputs=[sample(seed,'demo',i) for i in range(demos)]
    query_inputs=[sample(seed,'query',i) for i in range(queries)]
    pairs=lambda values:[{'input':g,'output':solve(g,turn)} for g in values]
    return {'train':pairs(demo_inputs),'test':pairs(query_inputs),'program_solution':program(setting)}


def survivors(train,setting):
    turn=settings(setting);result=['intended']
    for name in RIVALS:
        if all(solve(pair['input'],turn,rival=name)==pair['output'] for pair in train):result.append(name)
    return result


def input_errors(value):
    try:
        state=derive(value)
        if len(state['segments'])<1:return ['No diagonal signal segment']
        if len(state['triggers'])<1:return ['No active red trigger']
        return []
    except ValueError as exc:return [str(exc)]


def public_view(episode,query_index):
    integer(query_index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
            'test':[{'input':grid(episode['test'][query_index]['input'])}]}


def presentation_order(presentation_seed):
    integer(presentation_seed,0,2**63-1,'presentation seed')
    order=list(range(4));random.Random(f'db695cfb-presentation-v1:{presentation_seed}').shuffle(order);return order


def public_turns(seed,setting,demos,presentation_seed=0,count=4):
    integer(count,1,4,'presentation count');episode=generate(seed,setting,demos,4)
    integer(presentation_seed,0,2**63-1,'presentation seed')
    return [public_view(episode,i) for i in presentation_order(seed^presentation_seed)[:count]]
