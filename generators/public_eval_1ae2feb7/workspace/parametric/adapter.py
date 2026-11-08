"""Run-length pulse superposition. Pure standard library, exact local resources.

Labels returned by generate are Python claims; preflight/self_audit independently
execute the exact setting program in protected Racket. No official grids or gold
are imported by this module. Settings, programs, and complete banks are private.
"""
from __future__ import annotations
from copy import deepcopy
from itertools import groupby
from pathlib import Path
import random

PARAMETER = 'pulse_phase'
VALUES = ('leading', 'trailing')
DEFAULT = {PARAMETER: VALUES[0]}
DEMO_DIMS = ((12,19),(13,21),(14,23),(16,25),(18,26),(20,28))
QUERY_DIMS = ((12,20),(16,24),(24,28),(30,30))
RIVALS = ('opposite_phase','identity','nearest_only','farthest_only',
          'reverse_priority','period_plus_one','period_minus_one',
          'always_right','fixed_red_separator','gap_as_period','absolute_phase')


def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if type(value) is not list or not 1 <= len(value) <= 30 or type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
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
    phase=settings(setting)
    text=Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
    old="(define pulse-phase 'leading)"
    if text.count(old)!=1: raise ValueError('Canonical phase anchor drifted')
    return text if phase=='leading' else text.replace(old,"(define pulse-phase 'trailing)")


def separator(g):
    def score(c):
        return max((len(list(vs)) for color,vs in groupby(row[c] for row in g) if color),default=0)
    scores=[score(c) for c in range(len(g[0]))]
    return max(range(len(scores)),key=lambda c:scores[c])


def derive(g):
    """A: separator and ordered (color, period, near-gap) run records per row."""
    wall=separator(g); width=len(g[0]); records=[]
    for r,row in enumerate(g):
        left=any(row[:wall]); right=any(row[wall+1:])
        if not (left or right): continue
        direction=1 if left else -1
        source=row[:wall] if left else row[wall+1:][::-1]
        runs=[]; start=0
        for color,values in groupby(source):
            length=len(list(values))
            if color: runs.append((color,length,len(source)-start-length))
            start+=length
        records.append({'row':r,'direction':direction,'runs':runs,
                        'target_length':width-wall-1 if left else wall})
    return {'separator':wall,'rows':records}


def solve(value, phase='leading', *, rival=None):
    g=grid(value)
    if type(phase) is not str or phase not in VALUES: raise ValueError('Unknown pulse phase')
    if rival is not None and rival not in RIVALS: raise ValueError('Unknown rival')
    state=derive(g); wall=state['separator']; out=deepcopy(g)
    if rival=='identity':return out
    if rival=='fixed_red_separator' and sum(row[wall]==2 for row in g)<len(g)-1:return out
    if rival=='opposite_phase':phase=VALUES[1-VALUES.index(phase)]
    for rec in state['rows']:
        direction=rec['direction']; r=rec['row']; runs=rec['runs']
        if rival=='always_right' and direction<0:continue
        if rival=='nearest_only':runs=runs[-1:]
        if rival=='farthest_only':runs=runs[:1]
        if rival=='reverse_priority':runs=runs[::-1]
        for color,period,near_gap in runs:
            if rival=='period_plus_one':period+=1
            if rival=='period_minus_one':period=max(1,period-1)
            if rival=='gap_as_period':period+=near_gap
            offset=0 if phase=='leading' else period-1
            for k in range(rec['target_length']):
                c=wall+direction*(k+1)
                index=c if rival=='absolute_phase' else k
                if index%period==offset:out[r][c]=color
    return out


def sample(seed, stream, index):
    integer(seed,0,2**63-1,'seed')
    if stream not in ('demo','query'):raise ValueError('Unknown stream')
    dims=DEMO_DIMS if stream=='demo' else QUERY_DIMS
    integer(index,0,len(dims)-1,'index')
    h,w=dims[index]
    rng=random.Random(f'pulse-v1:{seed}:{stream}:{index}')
    sw=rng.choice((8,10)) if stream=='demo' and index==0 else rng.randint(7,min(11,w-8))
    # Odd first target column makes the solo period-two row refute absolute
    # column parity under BOTH phases, rather than relying on lucky offsets.
    rail_color=(rng.choice([1,3,4,5,6,7,8,9]) if index==0 else 2 if index==1 else rng.randint(1,9))
    g=[[0]*w for _ in range(h)]
    for row in g:row[sw]=rail_color
    # A blank penultimate row breaks accidental source columns. The final row is
    # sometimes a missing rail endpoint, matching the supplied shortened rail.
    if index%2:g[-1][sw]=0
    patterns=((3,2),(2,3),(4,),(1,),(2,),(4,1),(1,4),(2,1,2),(3,1,1))
    active=[r for r in range(h) if r not in (1,h-2) and not (r==h-1 and index%2)]
    rng.shuffle(active)
    for n,r in enumerate(active):
        lens=patterns[n%len(patterns)]
        colors=rng.sample(range(1,10),len(lens))
        maxgap=sw-sum(lens)
        gaps=[0]*(len(lens)+1)
        # Gaps are irrelevant to period. Ensure one offset long-run witness.
        if len(lens)==1 and lens[0]>1 and maxgap:
            gaps[-1]=rng.randint(1,min(2,maxgap));maxgap-=gaps[-1]
        if len(lens)>1 and maxgap and n%2:
            j=rng.randrange(1,len(lens));gaps[j]=1;maxgap-=1
        gaps[0]=rng.randint(0,maxgap)
        x=gaps[0]
        for i,(color,length) in enumerate(zip(colors,lens)):
            g[r][x:x+length]=[color]*length;x+=length+gaps[i+1]
    # Keep both orientations in the minimum teaching prefix, regardless of seed.
    if index%2:g=[row[::-1] for row in g]
    return g


def generate(seed, setting, demos, queries):
    integer(seed,0,2**63-1,'seed'); phase=settings(setting)
    integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    def pairs(stream,count):
        result=[]
        for index in range(count):
            inp=sample(seed,stream,index)
            result.append({'input':inp,'output':solve(inp,phase)})
        return result
    return {'train':pairs('demo',demos),'test':pairs('query',queries),
            'program_solution':program(setting)}


def survivors(train, setting):
    phase=settings(setting); answer=['intended']
    for name in RIVALS:
        if all(solve(p['input'],phase,rival=name)==p['output'] for p in train):answer.append(name)
    return answer


def public_view(episode, query_index):
    integer(query_index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
            'test':[{'input':grid(episode['test'][query_index]['input'])}]}


def presentation_order(presentation_seed):
    integer(presentation_seed,0,2**63-1,'presentation seed')
    order=list(range(4)); random.Random(f'pulse-presentation-v1:{presentation_seed}').shuffle(order)
    return order


def public_turns(seed, setting, demos, presentation_seed=0, count=4):
    integer(count,1,4,'presentation count')
    episode=generate(seed,setting,demos,4)
    integer(presentation_seed,0,2**63-1,'presentation seed')
    return [public_view(episode,i) for i in presentation_order(seed ^ presentation_seed)[:count]]
