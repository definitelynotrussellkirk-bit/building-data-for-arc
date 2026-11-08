"""Framed periodic-strip denoising and input-dependent anomaly marking.

The reference is a minimum-Hamming periodic decoder, NOT a parent-grid lookup.
The sampler independently draws a clean motif and corrupts it; rejection checks
that the declared decoder recovers that motif. Python labels are claims until
protected Racket executes them.
"""
from __future__ import annotations
import copy
import hashlib
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from puzzle_generators.base import gen_ctx

TASK = 'public_eval_135a2760'
VERSION = '1.0.0'
MODES = ('restore', 'mark_errors')
RIVALS = ('identity','period_2','period_3','first_repeat','horizontal_only',
          'vertical_only','first_panel_only','constant_per_lane')
BASE = Path(__file__).resolve().parent


def _integer(x, low, high, name):
    if type(x) is not int or not low <= x <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return x


def validate_grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
        or not 1 <= len(g[0]) <= 30 or any(type(row) is not list or len(row) != len(g[0])
        or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 integer color grid')
    return g


def _mode(values):
    counts = Counter(values)
    return min(counts, key=lambda v: (-counts[v], v))


def _candidate(seq, p, first=False):
    n, width = len(seq), len(seq[0])
    motif = [list(seq[i]) if first else [_mode([seq[j][c] for j in range(i,n,p)])
              for c in range(width)] for i in range(p)]
    prediction = [motif[i % p] for i in range(n)]
    cost = sum(a != b for x,y in zip(seq,prediction) for a,b in zip(x,y))
    return cost, motif, prediction


def analyze(g, forced_period=None, first=False):
    """Recover each panel's period, motif, prediction and mismatching coordinates."""
    validate_grid(g)
    h,w = len(g),len(g[0]); frame = g[0][0]
    rr = [r for r in range(h) if all(v==frame for v in g[r])]
    cc = [c for c in range(w) if all(g[r][c]==frame for r in range(h))]
    if not rr or not cc or rr[0]!=0 or rr[-1]!=h-1 or cc[0]!=0 or cc[-1]!=w-1:
        raise ValueError('A complete uniform outer frame is required')
    panels=[]
    for r0,r1 in zip(rr,rr[1:]):
        for c0,c1 in zip(cc,cc[1:]):
            if r1-r0<4 or c1-c0<4: continue
            ring=g[r0+1][c0+1]
            boundary=[(r,c) for r in range(r0+1,r1) for c in range(c0+1,c1)
                      if r in (r0+1,r1-1) or c in (c0+1,c1-1)]
            if ring==frame or any(g[r][c]!=ring for r,c in boundary):
                raise ValueError('Panel ring must be uniform and distinct from frame')
            ra,rb,ca,cb=r0+2,r1-1,c0+2,c1-1
            horizontal=cb-ca>=rb-ra
            seq=([[g[r][c] for r in range(ra,rb)] for c in range(ca,cb)] if horizontal
                 else [[g[r][c] for c in range(ca,cb)] for r in range(ra,rb)])
            n=len(seq)
            if n<4: raise ValueError('Periodic strips require length at least four')
            periods=[forced_period] if forced_period is not None else range(1,n//2+1)
            candidates=[(p,*_candidate(seq,p,first=first)) for p in periods if 1<=p<=n]
            p,cost,motif,pred=min(candidates,key=lambda x:(x[1],x[0]))
            cells=[(ra+j,ca+i,pred[i][j]) if horizontal else (ra+i,ca+j,pred[i][j])
                   for i in range(n) for j in range(len(seq[0]))]
            panels.append({'bbox':[ra,ca,rb-1,cb-1], 'horizontal':horizontal,
                           'period':p,'motif':motif,'ring':ring,'cost':cost,
                           'cells':cells,'corrections':[(r,c,v) for r,c,v in cells if g[r][c]!=v]})
    if not panels: raise ValueError('No lawful framed periodic strip found')
    return panels


def _render(g, panels, mode):
    out=copy.deepcopy(g)
    for panel in panels:
        for r,c,v in panel['corrections']:
            out[r][c]=v if mode=='restore' else panel['ring']
    return out


def solve(g, mode='restore'):
    if mode not in MODES: raise ValueError('Undeclared repair mode')
    return _render(g,analyze(g),mode)


def rival_solve(g,mode,rival):
    if rival not in RIVALS: raise ValueError('Unknown rival')
    if rival=='identity': return copy.deepcopy(g)
    forced={'period_2':2,'period_3':3,'constant_per_lane':1}.get(rival)
    panels=analyze(g,forced_period=forced)
    if rival=='first_repeat':
        # Keep the inferred period, but blindly copy its first observed repeat.
        panels=[analyze(g,forced_period=x['period'],first=True)[i] for i,x in enumerate(panels)]
    if rival=='horizontal_only': panels=[x for x in panels if x['horizontal']]
    if rival=='vertical_only': panels=[x for x in panels if not x['horizontal']]
    if rival=='first_panel_only': panels=panels[:1]
    return _render(g,panels,mode)


def _settings(settings):
    if type(settings) is not dict or set(settings)!={'repair_mode'} or settings['repair_mode'] not in MODES:
        raise ValueError('Expected exactly repair_mode=restore or mark_errors')
    return settings['repair_mode']


def program(settings):
    mode=_settings(settings)
    return (BASE/('canonical.rkt' if mode=='restore' else 'mark_errors.rkt')).read_text()


def _transpose(g):
    return [list(x) for x in zip(*g)]


@lru_cache(maxsize=4096)
def _sample_frozen(seed,index,stress):
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    rng=ctx.draw_rng('periodic_structural_grammar')
    for attempt in range(256):
        if stress:
            n=26; widths=[4,4,4,5]
        else:
            n=rng.randint(19,26)
            widths=[rng.randint(1,4) for _ in range(2+(index%2))]
        frame,ring=rng.sample(range(10),2)
        palette=[x for x in range(10) if x not in (frame,ring)]
        height=1+sum(t+3 for t in widths)
        clean=[[frame]*(n+4) for _ in range(height)]
        corrupt=copy.deepcopy(clean); r0=0
        for k,t in enumerate(widths):
            r1=r0+t+3
            for r in range(r0+1,r1):
                for c in range(1,n+3): clean[r][c]=corrupt[r][c]=ring
            p=(2,3,4,6)[(index+k)%4]
            ink=rng.choice(palette)
            motif=[[ink if rng.random()<.5 else frame for _ in range(t)] for _ in range(p)]
            # A primitive motif and both foreground/background are essential.
            if len({v for row in motif for v in row})<2: break
            seq=[motif[i%p] for i in range(n)]
            if any(_candidate(seq,q)[0]==0 for q in range(1,p)): break
            for i in range(n):
                for j in range(t): clean[r0+2+j][i+2]=corrupt[r0+2+j][i+2]=seq[i][j]
            # Corrupt the first repeat as well as later copies on broad strips.
            sites=[(rng.randrange(p),rng.randrange(t))]
            if t>=3:
                sites.append((rng.randrange(2*p,n),rng.randrange(t)))
            for i,j in sites:
                corrupt[r0+2+j][i+2]=frame if seq[i][j]==ink else ink
            r0=r1
        else:
            if index%2:
                clean,corrupt=_transpose(clean),_transpose(corrupt)
            if solve(corrupt,'restore')==clean:
                return tuple(tuple(row) for row in corrupt)
    raise RuntimeError('Could not sample an identifiable periodic scene in 256 bounded attempts')


def sample(seed,index,stress=False):
    _integer(seed,0,2**63-1,'seed'); _integer(index,0,2**31-1,'index')
    if type(stress) is not bool: raise ValueError('stress must be boolean')
    return [list(row) for row in _sample_frozen(seed,index,stress)]


def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed'); _integer(demos,2,6,'demos'); _integer(queries,1,4,'queries')
    mode=_settings(settings)
    # Count-independent streams preserve demo/query prefixes and setting matches.
    ins=[sample(seed,i) for i in range(demos)]
    tests=[sample(seed,100+i,stress=(i==3)) for i in range(queries)]
    if len({json.dumps(g) for g in ins+tests})!=len(ins)+len(tests):
        raise RuntimeError('Duplicate input in bounded generated lesson')
    return {'train':[{'input':g,'output':solve(g,mode)} for g in ins],
            'test':[{'input':g,'output':solve(g,mode)} for g in tests],
            'program_solution':program(settings)}


def public_turn(episode,turn,presentation_seed):
    """Controller projection: shuffle full bank before selecting a single turn.

    Neither IDs nor public bytes depend on labels, programs, hidden settings or
    episode metadata. The caller retains the whole bank and reveals one view.
    """
    _integer(turn,0,3,'turn'); _integer(presentation_seed,0,2**63-1,'presentation_seed')
    if len(episode['test'])!=4: raise ValueError('Present from the complete four-query bank')
    order=sorted(range(4),key=lambda i:hashlib.sha256(f'{presentation_seed}:{i}'.encode()).digest())
    return {'train':[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])}
                     for p in episode['train']],
            'test':[{'input':copy.deepcopy(episode['test'][order[turn]]['input'])}]}
