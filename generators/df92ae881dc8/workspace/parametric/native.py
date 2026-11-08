"""Period inference followed by canonical or doubled-spacing completion.

This is an independent Python claim model, not the labeling authority. Each
native setting is materialized as Racket and independently qualified there.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import random

HOME=Path(__file__).resolve().parent
MODES=('observed','doubled')
COLORS=(1,2,3,4,6,7,8,9)
DIRECTIONS=((-1,-1),(-1,1),(1,-1),(1,1))
POLICIES=('normal','fixed_2','fixed_3','fixed_4','min_gap','max_gap','first_gap',
          'last_gap','rows_only','cols_only','top_left_run','leftmost_run',
          'first_direction','last_direction','up_only','down_only','left_l_only',
          'right_l_only','right_columns','left_columns','both_columns',
          'raw_coverage','last_coverage_tie','no_extension','no_gray')


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def mode_of(settings):
    if type(settings) is not dict or set(settings)!={'spacing'}:
        raise ValueError('settings must name exactly spacing')
    mode=settings['spacing']
    if type(mode) is not str or mode not in MODES:
        raise ValueError('unknown spacing')
    return mode


def _longest(values):
    best=run=0
    for v in values:
        run=run+1 if v else 0
        best=max(best,run)
    return best


def _validate(g):
    if (type(g) is not list or not 6<=len(g)<=30 or type(g[0]) is not list
            or not 6<=len(g[0])<=30):
        raise ValueError('dimensions must be 6..30')
    w=len(g[0])
    if any(type(row) is not list or len(row)!=w or
           any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('rectangular exact-integer color grid required')
    colors={v for row in g for v in row if v}
    if len(colors)!=1 or next(iter(colors)) not in COLORS:
        raise ValueError('one nonzero non-gray foreground color required')
    fg=next(iter(colors))
    count=sum(v==fg for row in g for v in row)
    if count<6 or count==len(g)*w:
        raise ValueError('at least six foreground cells and a zero background required')
    return fg


def _runs(g,fg):
    runs=[]
    for r,row in enumerate(g):
        c=0
        while c<len(row):
            if row[c]!=fg:
                c+=1;continue
            start=c
            while c+1<len(row) and row[c+1]==fg:c+=1
            runs.append([r,start,c,c-start+1]);c+=1
    return runs


def _grow(cells,run,period,h,w,rs,cs):
    r0,start,end,_=run
    base=end if cs==1 else start
    painted=list(cells)
    k=1
    while True:
        r=r0+rs*period*k
        c=base+cs*period*k
        if not 0<=r<h:break
        if 0<=c<w:
            painted.extend((r,x) for x in (range(c+1) if cs==1 else range(c,w)))
            painted.extend((y,c) for y in (range(r+1) if rs==1 else range(r,h)))
        else:
            painted.extend((r,x) for x in range(w))
        k+=1
    return set(painted),len(painted)


def analyze(g,mode='observed',policy='normal'):
    if mode not in MODES or policy not in POLICIES:
        raise ValueError('unknown mode/policy')
    fg=_validate(g);h,w=len(g),len(g[0])
    cells={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==fg}
    sr=[r for r in range(h) if _longest([v==fg for v in g[r]])>=3]
    sc=[c for c in range(w) if _longest([g[r][c]==fg for r in range(h)])>=3]
    gaps=lambda seq:[b-a for a,b in zip(seq,seq[1:]) if 2<=b-a<=4]
    diffs=gaps(sr)+gaps(sc)
    counts=Counter(diffs)
    observed=next((d for d in diffs if counts[d]==max(counts.values())),2)
    chosen=observed
    if policy.startswith('fixed_'):chosen=int(policy[-1])
    elif policy in ('rows_only','cols_only'):
        subset=gaps(sr if policy=='rows_only' else sc)
        cc=Counter(subset)
        chosen=next((d for d in subset if cc[d]==max(cc.values())),2)
    elif diffs and policy in ('min_gap','max_gap','first_gap','last_gap'):
        chosen={'min_gap':min(diffs),'max_gap':max(diffs),'first_gap':diffs[0],'last_gap':diffs[-1]}[policy]
    p=chosen*(2 if mode=='doubled' else 1)
    full=[c for c in range(w) if all(g[r][c]==fg for r in range(h))]
    longruns=[r for r in _runs(g,fg) if r[3]>=3]
    if not full and not longruns:
        raise ValueError('need a full column or a horizontal run of length >=3')
    result={'observed_period':observed,'effective_period':p,'valid_gaps':diffs,
            'significant_rows':sr,'significant_cols':sc,'foreground':fg,'full_columns':full,
            'directions':[],'chosen_run':None,'winner':None}
    complete=set(cells)
    if full:
        result['branch']='full_columns'
        for c in full:
            anycol=lambda x:0<=x<w and any(g[r][x]==fg for r in range(h))
            if anycol(c-p) and c+p<w:direction=1
            elif anycol(c+p) and c-p>=0:direction=-1
            elif c+p<w:direction=1
            else:direction=-1
            if policy=='right_columns':direction=1
            elif policy=='left_columns':direction=-1
            result['directions'].append(direction)
            for d in (-1,1) if policy=='both_columns' else (direction,):
                x=c+d*p
                while 0<=x<w:
                    complete.update((r,x) for r in range(h));x+=d*p
    else:
        result['branch']='nested_l'
        key=(lambda r:(-r[3],r[0],r[1])) if policy=='top_left_run' else (
             (lambda r:(-r[3],-r[0],r[1])) if policy=='leftmost_run' else
             (lambda r:(-r[3],-r[0],-r[1])))
        run=min(longruns,key=key); result['chosen_run']=run
        choices=[_grow(cells,run,p,h,w,*direction) for direction in DIRECTIONS]
        allowed=list(range(4))
        if policy=='first_direction':allowed=[0]
        elif policy=='last_direction':allowed=[3]
        elif policy=='up_only':allowed=[0,1]
        elif policy=='down_only':allowed=[2,3]
        elif policy=='left_l_only':allowed=[0,2]
        elif policy=='right_l_only':allowed=[1,3]
        score=lambda i:choices[i][1] if policy=='raw_coverage' else len(choices[i][0])
        if policy=='last_coverage_tie':allowed.reverse()
        winner=max(allowed,key=score)
        complete=choices[winner][0]
        result['winner']=list(DIRECTIONS[winner]);result['candidate_sizes']=[len(x[0]) for x in choices]
    if policy=='no_extension':complete=set(cells)
    result['complete_cells']=sorted(complete)
    return result


def predict(g,mode='observed',policy='normal'):
    f=analyze(g,mode,policy);complete=set(map(tuple,f['complete_cells']))
    bg=0 if policy=='no_gray' else 5
    return [[f['foreground'] if (r,c) in complete else bg for c in range(len(g[0]))] for r in range(len(g))]


def _replace_once(source,old,new):
    if source.count(old)!=1:raise ValueError('canonical program site changed; reassess mutation')
    return source.replace(old,new,1)


def program(settings,*,policy='normal'):
    mode=mode_of(settings)
    source=(HOME/'canonical.rkt').read_text()
    if mode=='observed' and policy=='normal':return source
    allowed=('normal','fixed_2','fixed_3','fixed_4','min_gap','max_gap','first_gap','last_gap','top_left_run','leftmost_run','raw_coverage','last_coverage_tie')
    if policy not in allowed:raise ValueError('this audit policy has no Racket materialization')
    source=_replace_once(source,'(define period\n','(define observed-period\n')
    observed=policy[-1] if policy.startswith('fixed_') else 'observed-period'
    expression=f'(* 2 {observed})' if mode=='doubled' else observed
    source=_replace_once(source,'     (define full-cols',f'     (define period {expression})\n     (define full-cols')
    replacements={'min_gap':'(apply min diffs)','max_gap':'(apply max diffs)',
                  'first_gap':'(first diffs)','last_gap':'(last diffs)'}
    if policy in replacements:source=_replace_once(source,'(mode-list diffs)',replacements[policy])
    if policy=='raw_coverage':
        source=_replace_once(source,'(length (remove-duplicates cells))','(length cells)')
    if policy=='last_coverage_tie':
        source=_replace_once(source,'((rs (list -1 1)) (cs (list -1 1)))','((rs (list 1 -1)) (cs (list 1 -1)))')
    if policy in ('top_left_run','leftmost_run'):
        old='(- (+ (* 10000 (fourth run))\n                                           (* 100 (first run))\n                                           (second run)))'
        sign=100 if policy=='top_left_run' else -100
        source=_replace_once(source,old,f'(+ (* -10000 (fourth run)) (* {sign} (first run)) (second run))')
    return source


def _paint(g,row,start,length,color):
    for c in range(start,start+length):g[row][c]=color


def _full_lesson(rng):
    h=rng.randint(12,20);g=[[0]*30 for _ in range(h)];fg=rng.choice(COLORS)
    for c in (4,18):
        for row in g:row[c]=fg
    for c in (1,8,11,21,24,28):
        start=rng.randint(0,h-3)
        for r in range(start,start+3):g[r][c]=fg
    return g


def _l_lesson(rng,index):
    # Geometry-first construction, with an explicit known-valid fallback.
    # The coverage lesson retains nonuniform gaps and tied longest runs.
    for attempt in range(129):
        fg=rng.choice(COLORS)
        if index==1:
            if attempt==128:
                h,w,r,length,start,prior,short_a,short_b=24,19,12,6,7,1,4,11
            else:
                h=rng.choice((22,24,26,28));w=rng.randint(17,23);r=h//2
                length=rng.randint(5,7);start=rng.randint(5,min(9,w-length))
                prior=rng.randint(0,3);short_a=rng.randint(2,6);short_b=rng.randint(8,min(13,w-3))
            rows=((r-6,short_a,3),(r-4,prior,length),(r,start,length),(r+4,short_b,3))
            target=[-1,-1];rival='top_left_run'
        else:
            if attempt==128:
                h,w,length,start=28,22,5,8
                rows=((2,0,length),(2,start,length),(6,4,3),(8,19,3),(10,0,3))
            else:
                h,w=rng.choice((24,26,28,30)),rng.choice((22,24,26,28))
                length=rng.randint(4,6);start=rng.randint(length+1,min(14,w-length))
                rows=((2,0,length),(2,start,length),(6,rng.randint(0,w-3),3),
                      (8,rng.randint(0,w-3),3),(10,rng.randint(0,w-3),3))
            target=[1,1];rival='leftmost_run'
        g=[[0]*w for _ in range(h)]
        for y,x,n in rows:_paint(g,y,x,n,fg)
        if not all(analyze(g,mode)['winner']==(target if index==1 or mode=='observed' else [1,-1])
                   and predict(g,mode)!=predict(g,mode,rival) for mode in MODES):
            continue
        if index==1 and (predict(g,'observed')==predict(g,'observed','raw_coverage') or
                         predict(g,'doubled')==predict(g,'doubled','last_coverage_tie')):
            continue
        if index==2 and (predict(g,'observed')==predict(g,'observed','left_l_only') or
                         predict(g,'doubled')==predict(g,'doubled','right_l_only')):
            continue
        return g
    raise ValueError('validated fallback failed; check the independent rule model')


def _coverage_lesson(rng):
    # A real area tie at observed spacing; overlap changes the doubled winner.
    for attempt in range(129):
        fg=rng.choice(COLORS)
        if attempt==128:
            h,w,r,start,length,hint=16,27,1,18,8,3
        else:
            h=rng.randint(14,20);w=rng.randint(24,30);r=rng.randint(0,3)
            length=rng.randint(6,9);start=w-length-rng.randint(0,4)
            hint=rng.randint(0,w-3)
        g=[[0]*w for _ in range(h)]
        _paint(g,r,start,length,fg);_paint(g,r+4,hint,3,fg)
        if (predict(g,'observed')!=predict(g,'observed','last_coverage_tie') and
            predict(g,'doubled')!=predict(g,'doubled','raw_coverage') and
            predict(g,'doubled')!=predict(g,'doubled','left_l_only')):
            return g
    raise ValueError('validated coverage fallback failed')


def _full_query(rng,h,w,p,left=False):
    fg=rng.choice(COLORS);c=w-2 if left else p+1
    hint=c-p if left else c-p
    g=[[0]*w for _ in range(h)]
    for row in g:row[c]=fg
    start=rng.randint(0,h-3)
    for r in range(start,start+3):g[r][hint]=fg
    return g


def _l_query(rng,h,w):
    fg=rng.choice(COLORS);g=[[0]*w for _ in range(h)]
    p=rng.choice((2,3,4));r=rng.randint(0,h-p-1);length=rng.randint(4,min(9,w-1))
    _paint(g,r,rng.randint(0,w-length),length,fg)
    _paint(g,r+p,rng.randint(0,w-3),3,fg)
    return g


def _boundary(rng,branch):
    fg=rng.choice(COLORS);g=[[0]*30 for _ in range(30)]
    if branch==0:
        for c in (0,29):
            for row in g:row[c]=fg
        for c in (3,7,11,15,19,23,27):
            length=rng.randint(8,23);start=rng.randint(0,30-length)
            for r in range(start,start+length):g[r][c]=fg
    else:
        for i,r in enumerate(range(0,29,4)):
            length=rng.randint(15,27)
            start=0 if i%2==0 else 30-length
            _paint(g,r,start,length,fg)
        g[-1][0]=g[-1][-1]=fg
    return g


@lru_cache(maxsize=64)
def _bank(seed):
    rng=lambda name:random.Random(f'periodic-native:{seed}:{name}')
    demos=[_full_lesson(rng('demo0')),_l_lesson(rng('demo1'),1),_l_lesson(rng('demo2'),2)]
    demos.append(_coverage_lesson(rng('demo3')))
    r=rng('demo4');demos.append(_l_query(r,r.randint(13,21),r.randint(18,28)))
    r=rng('demo5');demos.append(_full_query(r,r.randint(20,28),r.randint(12,18),r.choice((2,3,4)),True))
    r=rng('query0');queries=[_full_query(r,6,6,2)]
    r=rng('query1');queries.append(_full_query(r,r.randint(14,26),r.randint(17,29),r.choice((2,3,4)),bool(seed%2)))
    r=rng('query2');queries.append(_l_query(r,r.randint(12,29),r.randint(12,29)))
    queries.append(_boundary(rng('query3'),seed%2))
    if len({json.dumps(g) for g in demos+queries})!=10:raise ValueError('input bank collision')
    return demos,queries


def generate(seed,settings,demos=4,queries=4):
    mode=mode_of(settings)
    integer(seed,0,2**63-1,'seed');integer(demos,4,6,'demos');integer(queries,1,4,'queries')
    train,test=deepcopy(_bank(seed))
    pairs=lambda grids:[{'input':g,'output':predict(g,mode)} for g in grids]
    return {'train':pairs(train[:demos]),'test':pairs(test[:queries]),'program_solution':program(settings)}


def teaching_check(episode,mode):
    checks=[]
    candidates=[(other,'normal') for other in MODES if other!=mode]+[(mode,p) for p in POLICIES]
    for candidate,policy in candidates:
        refuting=[i for i,p in enumerate(episode['train']) if predict(p['input'],candidate,policy)!=p['output']]
        different=[i for i,p in enumerate(episode['test']) if predict(p['input'],candidate,policy)!=p['output']]
        checks.append({'spacing':candidate,'policy':policy,'refuting_demos':refuting,'different_queries':different})
    return {'checks':checks,'ambiguous':[c for c in checks if not c['refuting_demos'] and c['different_queries']]}
