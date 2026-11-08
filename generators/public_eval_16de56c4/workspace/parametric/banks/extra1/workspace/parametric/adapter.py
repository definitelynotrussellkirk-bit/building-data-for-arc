"""Periodic row/column signals with episode-fixed marker resolution.

A scene first chooses the axis supported by the largest number of same-color
pairs.  Each pair defines an arithmetic progression.  In the canonical rule,
a unique differently colored cell on that progression resolves the signal:
its color replaces the pair and the painted span is bounded by the observed
marker and pair.  Without such a marker the pair color repeats to both canvas
boundaries.  The alternate setting ignores marker resolution and extends the
pair color through the whole progression.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import json
import random

PARAMETER='marker_policy'
VALUES=('resolve','pair_extends')
DEFAULT={PARAMETER:'resolve'}
DEMO_DIMS=((9,13),(12,10),(13,17),(16,19),(19,23),(22,27))
QUERY_DIMS=((12,15),(18,21),(24,27),(30,30))
RIVALS=('other_setting','always_horizontal','always_vertical','marker_color_full',
        'pair_color_bounded','step_one','endpoint_only','first_signal_only',
        'last_signal_only','ignore_marker_preserve','identity')
HERE=Path(__file__).resolve().parent


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list or not 1<=len(value[0])<=30:
        raise ValueError('Expected a nonempty grid of at most 30x30')
    width=len(value[0])
    if any(type(row) is not list or len(row)!=width or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value):
        raise ValueError('Expected rectangular exact integer colors 0..9')
    return deepcopy(value)


def settings(value):
    if type(value) is not dict or set(value)!={PARAMETER} or type(value[PARAMETER]) is not str or value[PARAMETER] not in VALUES:
        raise ValueError(f'Expected exactly {PARAMETER} in {VALUES}')
    return value[PARAMETER]


def program(setting):
    mode=settings(setting)
    name='canonical.rkt' if mode=='resolve' else 'pair_extends.rkt'
    return (HERE/name).read_text(encoding='utf-8')


def counterfactual_program(setting):
    settings(setting)
    return (HERE/'wrong_axis.rkt').read_text(encoding='utf-8')


def _axis_records(g,axis):
    h,w=len(g),len(g[0]);horizontal=axis=='horizontal'
    nlines=h if horizontal else w;length=w if horizontal else h
    records=[]
    for line in range(nlines):
        values=[g[line][p] if horizontal else g[p][line] for p in range(length)]
        positions=defaultdict(list)
        for p,v in enumerate(values):
            if v:positions[v].append(p)
        repeated=[(color,ps) for color,ps in positions.items() if len(ps)==2]
        for color,ps in sorted(repeated):
            a,b=ps;step=b-a
            markers=[(p,v) for p,v in enumerate(values)
                     if v and v!=color and (p-a)%step==0]
            records.append({'axis':axis,'line':line,'color':color,'a':a,'b':b,
                            'step':step,'marker':list(markers[0]) if len(markers)==1 else None,
                            'aligned_markers':[list(x) for x in markers]})
    return records


def derive(value,*,forced_axis=None):
    g=grid(value);h,w=len(g),len(g[0])
    horizontal=_axis_records(g,'horizontal');vertical=_axis_records(g,'vertical')
    if forced_axis is None:
        if len(horizontal)==len(vertical):
            raise ValueError('Expected one axis to have strictly more same-color pairs')
        axis='horizontal' if len(horizontal)>len(vertical) else 'vertical'
    else:
        if forced_axis not in ('horizontal','vertical'):raise ValueError('Unknown forced axis')
        axis=forced_axis
    records=horizontal if axis=='horizontal' else vertical
    if not records:raise ValueError('Expected at least one repeated-color signal pair')
    by_line=Counter(r['line'] for r in records)
    if any(n!=1 for n in by_line.values()):
        raise ValueError('Selected signal axis must contain at most one pair color per line')
    if any(len(r['aligned_markers'])>1 for r in records):
        raise ValueError('A signal may have at most one aligned differently colored marker')
    return {'height':h,'width':w,'axis':axis,'horizontal_pair_count':len(horizontal),
            'vertical_pair_count':len(vertical),'records':records}


def _paint_record(out,record,policy,*,rival=None):
    axis=record['axis'];line=record['line'];a=record['a'];b=record['b']
    step=1 if rival=='step_one' else record['step'];marker=record['marker']
    length=len(out[0]) if axis=='horizontal' else len(out)
    if rival=='endpoint_only':return
    use_marker=marker is not None and policy=='resolve'
    if rival=='marker_color_full':
        use_marker=marker is not None;bounded=False;paint=marker[1] if marker else record['color']
    elif rival=='pair_color_bounded':
        use_marker=marker is not None;bounded=bool(marker);paint=record['color']
    elif rival=='ignore_marker_preserve':
        use_marker=False;bounded=False;paint=record['color']
    else:
        bounded=use_marker;paint=marker[1] if use_marker else record['color']
    if bounded:
        lo=min(a,marker[0]);hi=max(b,marker[0]);positions=list(range(lo,hi+1,step))
    else:
        positions=[p for p in range(length) if (p-a)%step==0]
    for p in positions:
        if rival=='ignore_marker_preserve' and marker is not None and p==marker[0]:continue
        if axis=='horizontal':out[line][p]=paint
        else:out[p][line]=paint


def solve(value,policy='resolve',*,rival=None):
    g=grid(value)
    if type(policy) is not str or policy not in VALUES:raise ValueError('Unknown marker policy')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    if rival=='identity':return g
    if rival=='other_setting':policy='pair_extends' if policy=='resolve' else 'resolve'
    forced='horizontal' if rival=='always_horizontal' else 'vertical' if rival=='always_vertical' else None
    try:state=derive(g,forced_axis=forced)
    except ValueError:
        if forced is not None:return g
        raise
    records=state['records']
    if rival=='first_signal_only':records=records[:1]
    if rival=='last_signal_only':records=records[-1:]
    out=deepcopy(g)
    for record in records:_paint_record(out,record,policy,rival=rival)
    return out


def _rng(seed,role,index,attempt):
    return random.Random(f'16de56c4-periodic-v2:{seed}:{role}:{index}:{attempt}')


def _scene(seed,role,index,attempt):
    if role=='query':h,w=QUERY_DIMS[index]
    else:h,w=DEMO_DIMS[index%len(DEMO_DIMS)]
    rng=_rng(seed,role,index,attempt);g=[[0]*w for _ in range(h)]
    axis='horizontal' if index%2==0 else 'vertical'
    nlines=h if axis=='horizontal' else w;length=w if axis=='horizontal' else h
    if nlines<6 or length<9:raise ValueError('Profile too small')
    lines=sorted(rng.sample(range(1,nlines-1),4))
    palette=rng.sample(list(range(1,10)),9)
    bases=palette[:4];markers=palette[4:6];distractors=palette[6:9]
    steps=[2,3,1,4]
    for i,(line,color) in enumerate(zip(lines,bases)):
        step=min(steps[i],max(1,(length-1)//4))
        residues=[r for r in range(step) if len(range(r,length,step))>=5]
        if not residues:raise ValueError('No usable progression residue')
        residue=rng.choice(residues);seq=list(range(residue,length,step))
        if i<2:
            if len(seq)<5:raise ValueError('Marked progression too short')
            if (index+i)%2==0:
                pair=(seq[1],seq[2]);marker_pos=seq[-2]
            else:
                pair=(seq[-3],seq[-2]);marker_pos=seq[1]
            marker_color=markers[i]
        else:
            j=rng.randrange(0,len(seq)-1);pair=(seq[j],seq[j+1]);marker_pos=None
        for p in pair:
            if axis=='horizontal':g[line][p]=color
            else:g[p][line]=color
        if marker_pos is not None:
            if axis=='horizontal':g[line][marker_pos]=marker_color
            else:g[marker_pos][line]=marker_color
    # Unrelated singleton controls, each with a distinct color and off all pair lines.
    for color in distractors:
        for _ in range(64):
            r=rng.randrange(h);c=rng.randrange(w)
            if g[r][c]==0 and (r not in lines if axis=='horizontal' else c not in lines):
                g[r][c]=color;break
    state=derive(g)
    if state['axis']!=axis or len(state['records'])!=4:raise ValueError('Signal-axis construction drift')
    if solve(g,'resolve')==solve(g,'pair_extends'):raise ValueError('Settings alias')
    return g


def _raw_scene(seed,role,index):
    for attempt in range(256):
        try:return _scene(seed,role,index,attempt)
        except ValueError:pass
    raise ValueError('Bounded signal-scene search exhausted')


@lru_cache(maxsize=512)
def teaching(seed):
    integer(seed,0,2**63-1,'seed')
    for attempt in range(256):
        try:pair=(_scene(seed,'teach',0,attempt),_scene(seed,'teach',1,attempt))
        except ValueError:continue
        ok=True
        for value in VALUES:
            train=[{'input':deepcopy(g),'output':solve(g,value)} for g in pair]
            if survivors(train,{PARAMETER:value})!=['intended']:ok=False;break
        if ok:return deepcopy(pair)
    raise ValueError('Bounded teaching search could not refute declared rivals')


def sample(seed,role,index):
    integer(seed,0,2**63-1,'seed')
    if role not in ('demo','query'):raise ValueError('role must be demo or query')
    integer(index,0,5 if role=='demo' else 3,'index')
    if role=='demo' and index<2:return deepcopy(teaching(seed)[index])
    return _raw_scene(seed,role,index)


def generate(seed,setting,demos,queries):
    integer(seed,0,2**63-1,'seed');policy=settings(setting)
    integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    demo_inputs=[sample(seed,'demo',i) for i in range(demos)]
    query_inputs=[sample(seed,'query',i) for i in range(queries)]
    pairs=lambda values:[{'input':g,'output':solve(g,policy)} for g in values]
    return {'train':pairs(demo_inputs),'test':pairs(query_inputs),'program_solution':program(setting)}


def survivors(train,setting):
    policy=settings(setting);out=['intended']
    for rival in RIVALS:
        if all(solve(pair['input'],policy,rival=rival)==pair['output'] for pair in train):out.append(rival)
    return out


def input_errors(value):
    try:
        state=derive(value)
        if len(state['records'])<2:return ['Expected at least two signal lines']
        if not any(r['marker'] is not None for r in state['records']):return ['Expected at least one aligned marker']
        return []
    except ValueError as exc:return [str(exc)]


def public_view(episode,query_index):
    integer(query_index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
            'test':[{'input':grid(episode['test'][query_index]['input'])}]}


def presentation_order(seed):
    integer(seed,0,2**63-1,'presentation seed');order=list(range(4))
    random.Random(f'16de56c4-presentation-v1:{seed}').shuffle(order);return order


def public_turns(seed,setting,demos,presentation_seed=0,count=4):
    integer(count,1,4,'presentation count');integer(presentation_seed,0,2**63-1,'presentation seed')
    episode=generate(seed,setting,demos,4)
    return [public_view(episode,i) for i in presentation_order(seed^presentation_seed)[:count]]


def intermediate(value,setting):
    policy=settings(setting);state=derive(value)
    records=[]
    for rec in state['records']:
        rr=deepcopy(rec);rr['selected_policy']=policy
        records.append(rr)
    return {'axis':state['axis'],'horizontal_pair_count':state['horizontal_pair_count'],
            'vertical_pair_count':state['vertical_pair_count'],'records':records}


def dependency():
    return {'step_a':'Count same-color pairs on both axes, choose the majority axis, and derive each pair period, residue, and unique aligned marker.',
            'intermediate':'The selected axis plus ordered line records containing the pair color, period, residue, and optional marker coordinate/color.',
            'step_b':'Use each record and the episode marker policy to choose paint color and extent, then render the arithmetic progression.',
            'why_b_depends_on_a':'The cells painted by B are not fixed by the original pair endpoints alone: changing the derived global axis or period changes which progressions exist and therefore changes the final grid.'}
