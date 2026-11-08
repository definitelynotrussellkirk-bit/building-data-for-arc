"""Downward falling rays route around horizontal obstacles.

The exact parent setting splits at both obstacle ends.  The alternative keeps
only the closest exit to each impact column; ties choose the left exit.  Inputs
are generated independently of the setting and labels are later replayed by the
protected Racket runtime.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

PARAMETER='routing_mode'
VALUES=('split','closest_exit')
DEFAULT={PARAMETER:'split'}
DEMO_DIMS=((10,12),(12,14),(15,17),(18,20),(22,24),(26,28))
QUERY_DIMS=((12,14),(18,18),(24,26),(30,30))
RIVALS=('opposite_mode','identity','left_only','right_only','continue_through',
        'no_cap','cap_without_margin','stop_at_obstacle','first_source_only',
        'single_cell_obstacle','all_columns')


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if type(value) is not list or not 3<=len(value)<=30 or type(value[0]) is not list or not 3<=len(value[0])<=30:
        raise ValueError('Expected a nonempty grid of at most 30x30')
    if any(type(row) is not list or len(row)!=len(value[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value):
        raise ValueError('Expected rectangular exact integer colors 0..9')
    return deepcopy(value)


def parse_settings(value):
    if type(value) is not dict or set(value)!={PARAMETER} or type(value[PARAMETER]) is not str or value[PARAMETER] not in VALUES:
        raise ValueError(f'Expected exactly {PARAMETER} in {VALUES}')
    return value[PARAMETER]


def program(setting):
    mode=parse_settings(setting)
    text=Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
    anchor="(define routing-mode 'split)"
    if text.count(anchor)!=1:raise ValueError('Canonical routing anchor changed')
    return text if mode=='split' else text.replace(anchor,"(define routing-mode 'closest-exit)")


def segment_bounds(g,r,c,single=False):
    if single:return c,c
    w=len(g[0]);left=right=c
    while left>0 and g[r][left-1]==2:left-=1
    while right+1<w and g[r][right+1]==2:right+=1
    return left,right


def _paint(out,r,a,b):
    if r<0:return
    for c in range(max(0,a),min(len(out[0])-1,b)+1):
        if out[r][c]!=2:out[r][c]=6


def solve(value,mode='split',*,rival=None):
    g=grid(value)
    if type(mode) is not str or mode not in VALUES:raise ValueError('Unknown routing mode')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    if not any(v==6 for v in g[0]):raise ValueError('Expected at least one magenta source on the top edge')
    if any(v not in (2,6,7) for row in g for v in row):raise ValueError('Expected only red, magenta, and orange role colors')
    if rival=='identity':return g
    if rival=='opposite_mode':mode=VALUES[1-VALUES.index(mode)]
    h,w=len(g),len(g[0]);out=deepcopy(g)
    active=[c for c,v in enumerate(g[0]) if v==6]
    if rival=='first_source_only':active=active[:1]
    if rival=='all_columns':active=list(range(w))
    stopped=False
    for r in range(1,h):
        next_active=[];seen=set()
        for c in sorted(set(active)):
            if not 0<=c<w:continue
            if g[r][c]!=2:
                out[r][c]=6;next_active.append(c);continue
            if rival=='continue_through':
                next_active.append(c);continue
            if rival=='stop_at_obstacle':
                stopped=True;continue
            left,right=segment_bounds(g,r,c,single=rival=='single_cell_obstacle')
            if mode=='split' and rival not in ('left_only','right_only'):
                key=(left,right)
                if key in seen:continue
                seen.add(key)
                le,re=left-1,right+1
                if rival!='no_cap':
                    _paint(out,r-1,left if rival=='cap_without_margin' else le,
                           right if rival=='cap_without_margin' else re)
                if le>=0:out[r][le]=6;next_active.append(le)
                if re<w:out[r][re]=6;next_active.append(re)
            else:
                le,re=left-1,right+1
                if rival=='left_only':choose_left=le>=0
                elif rival=='right_only':choose_left=not (re<w)
                else:choose_left=(re>=w) or (le>=0 and c-le<=re-c)
                exit_col=le if choose_left else re
                if rival!='no_cap' and 0<=exit_col<w:
                    cap_end=(left if choose_left else right) if rival=='cap_without_margin' else exit_col
                    _paint(out,r-1,min(c,cap_end),max(c,cap_end))
                if 0<=exit_col<w:
                    out[r][exit_col]=6;next_active.append(exit_col)
        active=sorted(set(next_active))
        if stopped:active=[]
    return out


def derive(value,mode='split'):
    g=grid(value);h,w=len(g),len(g[0]);active=[c for c,v in enumerate(g[0]) if v==6];events=[]
    for r in range(1,h):
        next_active=[];seen=set()
        for c in sorted(set(active)):
            if g[r][c]!=2:next_active.append(c);continue
            left,right=segment_bounds(g,r,c);key=(left,right)
            if mode=='split':
                if key in seen:continue
                seen.add(key);exits=[x for x in (left-1,right+1) if 0<=x<w]
            else:
                le,re=left-1,right+1;choose_left=(re>=w) or (le>=0 and c-le<=re-c)
                exits=[le if choose_left else re]
            events.append({'row':r,'impact':c,'segment':[left,right],'exits':exits})
            next_active.extend(exits)
        active=sorted(set(next_active))
    return {'sources':[c for c,v in enumerate(g[0]) if v==6],'events':events,'final_active':active}


def input_errors(value):
    try:
        g=grid(value)
        if not any(v==6 for v in g[0]):return ['Expected at least one top-edge magenta source']
        if any(v not in (2,6,7) for row in g for v in row):return ['Unexpected role color']
        if any(v==6 for row in g[2:] for v in row):return ['Input magenta is reserved for the top source stem']
        if any(v==2 for v in g[0]):return ['Red obstacles may not occupy the source row']
        for r,row in enumerate(g):
            runs=[];c=0
            while c<len(row):
                if row[c]!=2:c+=1;continue
                start=c
                while c+1<len(row) and row[c+1]==2:c+=1
                runs.append((start,c));c+=1
            if r>0 and any(g[r-1][c]==2 for a,b in runs for c in range(a,b+1)):
                return ['Obstacle rows must be separated vertically']
    except (ValueError,TypeError,IndexError) as error:return [str(error)]
    return []


def _advance(active,bars,w,mode):
    next_active=[];seen=set()
    for c in sorted(set(active)):
        hit=next(((l,r) for l,r in bars if l<=c<=r),None)
        if hit is None:next_active.append(c);continue
        l,r=hit
        if mode=='split':
            if hit in seen:continue
            seen.add(hit);next_active.extend(x for x in (l-1,r+1) if 0<=x<w)
        else:
            le,re=l-1,r+1;choose_left=(re>=w) or (le>=0 and c-le<=re-c)
            x=le if choose_left else re
            if 0<=x<w:next_active.append(x)
    return sorted(set(next_active))


def sample(seed,stream,index,attempt=0):
    integer(seed,0,2**63-1,'seed');integer(attempt,0,4095,'attempt')
    if stream not in ('demo','query'):raise ValueError('Unknown stream')
    dims=DEMO_DIMS if stream=='demo' else QUERY_DIMS;integer(index,0,len(dims)-1,'index')
    h,w=dims[index];rng=random.Random(f'falling-ray-v2:{seed}:{stream}:{index}:{attempt}')
    g=[[7]*w for _ in range(h)]
    count=min(3,1+(index%3));sources=sorted(rng.sample(range(1,w-1),count))
    for c in sources:g[0][c]=g[1][c]=6
    split_active=sources[:];near_active=sources[:]
    rows=[];r=3
    target_count=max(3,min(9,(h-3)//2))
    while r<h-1 and len(rows)<target_count:
        rows.append(r);r+=rng.choice((2,3))
    for ordinal,r in enumerate(rows):
        union=sorted(set(split_active)|set(near_active))
        if not union:break
        target=union[(ordinal+rng.randrange(len(union)))%len(union)]
        max_left=min(target,6);max_right=min(w-1-target,6)
        left_span=rng.randint(0,max_left);right_span=rng.randint(0,max_right)
        if left_span==right_span:
            if right_span<max_right:right_span+=1
            elif left_span<max_left:left_span+=1
        if left_span+right_span<1:
            if target+1<w:right_span=1
            else:left_span=1
        l,rgt=target-left_span,target+right_span
        bars=[(l,rgt)]
        if w>=12 and rng.random()<0.55:
            choices=[]
            for _ in range(20):
                dl=rng.randrange(0,w-1);dr=min(w-1,dl+rng.randint(0,min(5,w-1-dl)))
                if dr<l-1 or dl>rgt+1:
                    choices.append((dl,dr));break
            bars+=choices
        for a,b in bars:
            for c in range(a,b+1):g[r][c]=2
        split_active=_advance(split_active,bars,w,'split')
        near_active=_advance(near_active,bars,w,'closest_exit')
    if not rows:raise ValueError('No obstacle rows generated')
    errors=input_errors(g)
    if errors:raise ValueError('; '.join(errors))
    if solve(g,'split')==solve(g,'closest_exit'):raise ValueError('Settings did not diverge')
    return g


@lru_cache(maxsize=64)
def teaching(seed):
    for attempt in range(256):
        try:
            grids=[sample(seed,'demo',i,attempt) for i in range(2)]
        except ValueError:
            continue
        ok=True
        for mode in VALUES:
            train=[{'input':g,'output':solve(g,mode)} for g in grids]
            if survivors(train,{PARAMETER:mode})!=['intended']:ok=False;break
        if ok:return tuple(tuple(tuple(row) for row in g) for g in grids)
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
    integer(seed,0,2**63-1,'presentation seed');order=list(range(4));random.Random(f'falling-ray-presentation-v1:{seed}').shuffle(order);return order


def public_turns(seed,setting,demos,presentation_seed=0,count=4):
    integer(count,1,4,'presentation count');integer(presentation_seed,0,2**63-1,'presentation seed')
    episode=generate(seed,setting,demos,4);order=presentation_order(seed^presentation_seed)
    return [public_view(episode,i) for i in order[:count]]
