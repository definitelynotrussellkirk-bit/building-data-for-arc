"""Complete directed pairs, then fill only newly enclosed zero regions."""
from __future__ import annotations
import copy
from collections import deque
import hashlib
from pathlib import Path
import random

TASK_ID='8de3465b4dbd'
KEY='closure_policy'
SETTINGS=('markers_only','newly_enclosed')
RIVALS=('markers_only','all_enclosed','enclosed_before','largest_new_only',
        'all_zero_after','ignore_reverse','ignore_blocked','first_per_row')
HERE=Path(__file__).resolve().parent
CANONICAL_SHA256='b3679e3b614ff63c5de6099ccf1013863a0d14456968b052874d8331d7f761ab'


def canonical():
    source=(HERE/'canonical.rkt').read_text()
    if hashlib.sha256(source.encode()).hexdigest()!=CANONICAL_SHA256:
        raise ValueError('canonical source drift')
    return source


def settings_value(settings):
    if type(settings) is not dict or set(settings)!={KEY} or settings[KEY] not in SETTINGS:
        raise ValueError('settings must contain exactly a supported closure_policy')
    return settings[KEY]


def program(settings): return rule_for(settings_value(settings))


def rule_for(name):
    source=canonical()
    if name=='markers_only': return source
    if name not in SETTINGS+RIVALS: raise ValueError('unknown rule')
    # Canonical rule! uses implicit g, so wrap its unchanged body in a lambda.
    body=source[len('(rule!'):-1].strip()
    if name=='ignore_reverse':
        body=body.replace('(and (= (at g r c) 2) (= (at g r (+ c 1)) 3)',
            '(and (or (and (= (at g r c) 2) (= (at g r (+ c 1)) 3)) (and (= (at g r c) 3) (= (at g r (+ c 1)) 2)))')
    if name=='ignore_blocked':
        body=body.replace('(= (at g r (+ c 2)) 0)', '#t')
    if name=='first_per_row':
        body='''(for/fold ([out g]) ([r (in-range (rows g))])
          (let* ((cs (filter (lambda (c) (and (= (at g r c) 2) (= (at g r (+ c 1)) 3) (= (at g r (+ c 2)) 0))) (range (- (cols g) 2)))))
            (if (null? cs) out (set-cell out r (+ (first cs) 2) 8))))'''
    select='eligible'
    if name=='all_enclosed': select='(filter (lambda (o) (not (boundary? o))) now)'
    elif name=='enclosed_before': select='(filter (lambda (o) (not (boundary? o))) old)'
    elif name=='largest_new_only': select="(if (null? eligible) '() (list (pick-max eligible obj-size)))"
    elif name=='all_zero_after': select='now'
    return f'''(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (marked ((lambda (g) {body}) g))
             (boundary? (lambda (o) (or (= (obj-r1 o) 0) (= (obj-c1 o) 0) (= (obj-r2 o) (- h 1)) (= (obj-c2 o) (- w 1)))))
             (zeros (lambda (grid) (filter (lambda (o) (= (obj-color o) 0)) (objects grid -1))))
             (old (zeros g))
             (old-open (apply append (map obj-cells (filter boundary? old))))
             (now (zeros marked))
             (eligible (filter (lambda (o) (and (not (boundary? o)) (member (first (obj-cells o)) old-open))) now)))
        (reduce (lambda (out o) (paint-cells out (obj-cells o) 4)) marked {select}))))'''


def zero_regions(g):
    h,w=len(g),len(g[0]);seen=set();regions=[]
    for r in range(h):
        for c in range(w):
            if g[r][c]!=0 or (r,c) in seen: continue
            todo=deque([(r,c)]);seen.add((r,c));cells=[]
            while todo:
                u,v=todo.popleft();cells.append((u,v))
                for a,b in ((u-1,v),(u+1,v),(u,v-1),(u,v+1)):
                    if 0<=a<h and 0<=b<w and g[a][b]==0 and (a,b) not in seen:
                        seen.add((a,b));todo.append((a,b))
            regions.append(cells)
    return regions


def boundary(cells,h,w):
    return any(r in (0,h-1) or c in (0,w-1) for r,c in cells)


def mark(g,mode='newly_enclosed'):
    out=copy.deepcopy(g)
    for r,row in enumerate(g):
        for c in range(len(row)-2):
            pair=(row[c],row[c+1])
            matching=pair==(2,3) or (mode=='ignore_reverse' and pair==(3,2))
            if matching and (row[c+2]==0 or mode=='ignore_blocked'):
                out[r][c+2]=8
                if mode=='first_per_row': break
    return out


def predict(g,name):
    if name not in SETTINGS+RIVALS: raise ValueError('unknown rule')
    out=mark(g,name)
    if name=='markers_only': return out
    h,w=len(g),len(g[0])
    old=zero_regions(g);now=zero_regions(out)
    exterior={p for cells in old if boundary(cells,h,w) for p in cells}
    selected=[cells for cells in now if not boundary(cells,h,w) and cells[0] in exterior]
    if name=='all_enclosed': selected=[cells for cells in now if not boundary(cells,h,w)]
    elif name=='enclosed_before': selected=[cells for cells in old if not boundary(cells,h,w)]
    elif name=='largest_new_only': selected=[max(selected,key=len)] if selected else []
    elif name=='all_zero_after': selected=now
    for cells in selected:
        for r,c in cells: out[r][c]=4
    return out


def _rng(seed,domain):
    return random.Random(int.from_bytes(hashlib.sha256(f'{TASK_ID}:{seed}:{domain}'.encode()).digest(),'big'))


def construct(seed,slot):
    rng=_rng(seed,f'scene:{slot}')
    h,w=(30,30) if slot==9 else (16+slot,20+rng.randrange(5))
    nrows=3 if slot==9 else 2
    g=[[0]*w for _ in range(h)]
    roles=['new1','new2','old','half'] if nrows==2 else ['new1','new2','old','half','reverse','new1']
    rng.shuffle(roles)
    expected=[]
    for k,role in enumerate(roles):
        rr,cc=divmod(k,2)
        r1=rr*(h//nrows)
        r2=(rr+1)*(h//nrows)-4 if rr<nrows-1 else h-1
        c1=0 if cc==0 else w//2+1
        c2=w//2-2 if cc==0 else w-1
        # Rectangular walls have a real two-dimensional interior.
        assert r2-r1>=4 and c2-c1>=5
        for r in range(r1,r2+1):
            for c in range(c1,c2+1):
                if r in (r1,r2) or c in (c1,c2): g[r][c]=3
        def gate(row,reverse=False,blocked=False):
            col=rng.randrange(c1+2,c2)
            g[row][col-2:col+1]=([3,2,0] if reverse else [2,3,3] if blocked else [2,3,0])
        if role=='old': gate(r1,blocked=True)
        else:
            gate(r1,reverse=role=='reverse')
            if role in ('new2','half'): gate(r2,reverse=role=='half')
        if role in ('new1','new2'):
            expected.extend((r,c) for r in range(r1+1,r2) for c in range(c1+1,c2))
    # Keep a full zero row on BOTH sides of these motifs: otherwise a motif
    # can plug a chamber gate from outside before the rule runs.
    # One separator row has exact, reversed and blocked freestanding motifs.
    # A trigger creates a marker here but cannot enclose a room.
    row=h//nrows-2
    g[row][0:3]=[2,3,0]
    g[row][5:8]=[3,2,0]
    g[row][w-3:w]=[2,3,3]
    return g, expected


def scene(seed,slot): return construct(seed,slot)[0]


def observe(g):
    out=mark(g);h,w=len(g),len(g[0]);old=zero_regions(g)
    exterior={p for cells in old if boundary(cells,h,w) for p in cells}
    new=[cells for cells in zero_regions(out) if not boundary(cells,h,w) and cells[0] in exterior]
    return {'input_shape':[h,w],'input_nonzero':sum(x!=0 for row in g for x in row),
            'old_regions':sum(not boundary(cells,h,w) for cells in old),
            'new_regions':len(new),'new_region_sizes':[len(c) for c in new],
            'new_marker_cells':[[r,c] for r in range(h) for c in range(w) if out[r][c]==8 and g[r][c]==0],
            'newly_enclosed_cells':[list(p) for cells in new for p in sorted(cells)]}


def generate(seed,settings,demos,queries):
    value=settings_value(settings)
    if type(seed) is not int or not 0<=seed<2**63: raise ValueError('invalid seed')
    if type(demos) is not int or not 2<=demos<=6: raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4: raise ValueError('queries must be 1..4')
    inputs=[scene(seed,i) for i in range(10)]
    order=list(range(4));_rng(seed,'presentation').shuffle(order)
    pair=lambda g:{'input':g,'output':predict(g,value)}
    return {'train':[pair(g) for g in inputs[:demos]],'test':[pair(inputs[6+i]) for i in order[:queries]],
            'program_solution':program(settings),'private':{'settings':copy.deepcopy(settings),'seed':seed,
            'query_source_indices':order[:queries],'training_admitted':False}}


def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']): raise ValueError('invalid query index')
    return {'train':copy.deepcopy(episode['train']),'test':[{'input':copy.deepcopy(episode['test'][index]['input'])}]}
