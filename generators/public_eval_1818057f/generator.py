"""Simultaneous plus detection and cross-bearing component selection."""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import copy
import hashlib
import random
import json
HERE=Path(__file__).resolve().parent
VALUES=('all','largest')
CROSS=((0,0),(-1,0),(1,0),(0,-1),(0,1))
DIAGONAL=((0,0),(-1,-1),(-1,1),(1,-1),(1,1))
RIVALS=('all_crosses','largest_cross_component','smallest_cross_component','first_component','last_component',
        'bbox_area','most_crosses','largest_any','eight_connected','centers_only','horizontal_only','vertical_only',
        'clear_diagonals','isolated_crosses','greedy_recolor','diagonal_cross','widest_component','tallest_component')

def integer(v,lo,hi,name):
    if type(v) is not int or not lo<=v<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return v

def validate_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(x) is not int or not 0<=x<=9 for x in row) for row in g)):
        raise ValueError('Need rectangular 1..30 grid with exact integer colors 0..9')

def components(points,eight=False):
    left=set(points);parts=[]
    steps=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc) and (eight or abs(dr)+abs(dc)==1)]
    while left:
        p=min(left);left.remove(p);part={p};q=[p]
        for r,c in q:
            for dr,dc in steps:
                t=(r+dr,c+dc)
                if t in left:left.remove(t);part.add(t);q.append(t)
        parts.append(part)
    return parts

def bbox(points):return min(r for r,c in points),min(c for r,c in points),max(r for r,c in points),max(c for r,c in points)

def parse(g,rival=None):
    validate_grid(g);h,w=len(g),len(g[0])
    fg={(r,c) for r in range(h) for c in range(w) if g[r][c]==4}
    parts=components(fg,eight=rival=='eight_connected');offsets=DIAGONAL if rival=='diagonal_cross' else CROSS
    centers={(r,c) for r in range(1,h-1) for c in range(1,w-1) if all((r+dr,c+dc) in fg for dr,dc in offsets)}
    if rival=='clear_diagonals':centers={p for p in centers if all((p[0]+dr,p[1]+dc) not in fg for dr,dc in DIAGONAL[1:])}
    if rival=='isolated_crosses':centers={p for p in centers if any(p in s and len(s)==5 for s in parts)}
    bearing=[s for s in parts if centers&s]
    return {'fg':fg,'parts':parts,'centers':centers,'bearing':bearing,'offsets':offsets}

def select(p,value,rival=None):
    parts=p['bearing'];mode={'all_crosses':'all','largest_cross_component':'largest',
        'smallest_cross_component':'smallest','first_component':'first','last_component':'last',
        'bbox_area':'bbox','most_crosses':'most','largest_any':'any','widest_component':'width','tallest_component':'height'}.get(rival,value)
    if mode=='any':return [max(p['parts'],key=len)] if p['parts'] else []
    if not parts:return []
    if mode=='all':return parts
    if mode=='largest':return [max(parts,key=len)]
    if mode=='smallest':return [min(parts,key=len)]
    if mode=='first':return parts[:1]
    if mode=='last':return parts[-1:]
    if mode=='most':return [max(parts,key=lambda s:len(s&p['centers']))]
    def measure(s):
        r0,c0,r1,c1=bbox(s)
        return (r1-r0+1)*(c1-c0+1) if mode=='bbox' else c1-c0+1 if mode=='width' else r1-r0+1
    return [max(parts,key=measure)]

def solve(g,value='all',rival=None):
    if value not in VALUES or (rival is not None and rival not in RIVALS):raise ValueError('Unknown rule')
    p=parse(g,rival);chosen=select(p,value,rival);centers=sorted(c for c in p['centers'] if any(c in s for s in chosen))
    out=copy.deepcopy(g)
    offsets={'centers_only':((0,0),),'horizontal_only':((0,0),(0,-1),(0,1)),
             'vertical_only':((0,0),(-1,0),(1,0))}.get(rival,p['offsets'])
    for r,c in centers:
        if rival=='greedy_recolor' and any(out[r+dr][c+dc]!=4 for dr,dc in CROSS):continue
        for dr,dc in offsets:out[r+dr][c+dc]=8
    return out

def self_check(g):
    try:validate_grid(g);return []
    except (ValueError,TypeError,IndexError) as e:return [str(e)]

def _rng(seed,tag):return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{tag}'.encode()).digest(),'big'))

def _transform(points,rng):
    ps=set(points)
    for _ in range(rng.randrange(4)):ps={(c,7-r) for r,c in ps}
    if rng.choice((False,True)):ps={(r,7-c) for r,c in ps}
    return ps

def _scene(seed,tag,stress=False,profile=None):
    rng=_rng(seed,tag);h=30 if stress else rng.randrange(24,30);w=30 if stress else rng.randrange(24,30)
    teaching=tag.startswith('demo:')
    bg=2 if teaching else rng.choice((0,1,2,3,5,6,7,9))
    g=[[bg]*w for _ in range(h)]
    # A large unrelated connected frame has no cross and must not win selection.
    if teaching or stress or rng.choice((True,False)):
        for r in range(h):g[r][0]=g[r][w-1]=4
        for c in range(w):g[0][c]=g[h-1][c]=4
    a={(3,c) for c in range(8)}|{(r,2) for r in range(6)}|{(5,3),(5,4),(2,3)}  # 16 cells, one cross
    b={(r,1) for r in range(7)}|{(1,0),(1,2)}|{(6,c) for c in range(2,7)}      # 14 cells, larger bbox
    which=rng.randrange(3) if profile is None else profile
    # This template wins by area in profile 1, but not profile 0. A different
    # random solid size in profile 2 varies the winning motif and ties explicitly.
    rh,cw=(3,4) if which==0 else (5,5) if which==1 else (rng.randrange(3,6),rng.randrange(3,7))
    compact={(r,c) for r in range(rh) for c in range(cw)}
    bridge={(r,c) for r in range(3) for c in range(3)}|{(r,c) for r in range(3,6) for c in range(3,6)}
    slots=[(3,3),(3,w-11),(h-11,3),(h-11,w-11)];rng.shuffle(slots)
    for original,(r0,c0) in zip((a,b,compact,bridge),slots):
        shape=set(original)
        if not teaching:
            # Grow irregular connected appendages, including new/overlapping
            # crosses. Source labels are computed from the resulting geometry.
            for _ in range(rng.randrange(2,16)):
                frontier=sorted({(r+dr,c+dc) for r,c in shape for dr,dc in CROSS[1:]
                    if 0<=r+dr<8 and 0<=c+dc<8 and (r+dr,c+dc) not in shape})
                if frontier:shape.add(rng.choice(frontier))
        for r,c in _transform(shape,rng):g[r0+r][c0+c]=4
    return g

@lru_cache(maxsize=128)
def _bank(seed):
    for attempt in range(256):
        ds=[_scene(seed,f'demo:{attempt}:{i}',profile=i) for i in range(2)]
        okay=True
        for value in VALUES:
            equivalent={'all_crosses','eight_connected'} if value=='all' else {'largest_cross_component'}
            for rival in RIVALS:
                if rival in equivalent:continue
                if all(solve(g,value,rival)==solve(g,value) for g in ds):okay=False;break
            if not okay:break
        if okay:break
    else:raise RuntimeError('Bounded distinguishing-demo search exhausted')
    ds += [_scene(seed,f'extra:{i}') for i in range(4)]
    qs=[_scene(seed,f'query:{i}',stress=i==3,profile=0 if i==3 else None) for i in range(4)]
    if len({json.dumps(g) for g in ds+qs})!=10:raise RuntimeError('Input collision')
    return ds,qs

def setting(settings):
    if type(settings) is not dict or set(settings)!={'selection'} or type(settings['selection']) is not str or settings['selection'] not in VALUES:raise ValueError('Expected exact selection=all|largest')
    return settings['selection']

def program(settings):return _program(setting(settings))

def _program(value,rival=None):
    sm={'all':0,'largest':1}[value]
    sm={'all_crosses':0,'largest_cross_component':1,'smallest_cross_component':2,'first_component':3,'last_component':4,'bbox_area':5,'most_crosses':6,'largest_any':7,'widest_component':8,'tallest_component':9}.get(rival,sm)
    dm={'clear_diagonals':1,'isolated_crosses':2,'diagonal_cross':3}.get(rival,0)
    pm={'centers_only':1,'horizontal_only':2,'vertical_only':3,'greedy_recolor':4}.get(rival,0)
    source=(HERE/'canonical.rkt').read_text()
    return source.replace('(define selection-mode 0)',f'(define selection-mode {sm})').replace('(define detection-mode 0)',f'(define detection-mode {dm})').replace('(define painting-mode 0)',f'(define painting-mode {pm})').replace('(define use-eight #f)',f"(define use-eight {'#t' if rival=='eight_connected' else '#f'})")

def rival_program(settings,rival):
    if rival not in RIVALS:raise ValueError('Unknown rival')
    return _program(setting(settings),rival)

def generate(seed,settings,demos=3,queries=4):
    integer(seed,0,2**63-1,'seed');integer(demos,2,6,'demos');integer(queries,1,4,'queries');v=setting(settings)
    ds,qs=copy.deepcopy(_bank(seed));label=lambda g:{'input':g,'output':solve(g,v)}
    return {'train':[label(g) for g in ds[:demos]],'test':[label(g) for g in qs[:queries]],'program_solution':program(settings)}

def present(seed,settings,demos=3,queries=4,presentation_seed=0):
    integer(queries,1,4,'queries');integer(presentation_seed,0,2**63-1,'presentation_seed')
    ep=generate(seed,settings,demos,4);order=list(range(4));_rng(seed,f'presentation:{presentation_seed}').shuffle(order)
    return {'public':[{'train':copy.deepcopy(ep['train']),'test':[{'input':copy.deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]],
            'private':{'settings':copy.deepcopy(settings),'seed':seed,'presentation_seed':presentation_seed,'source_indices':order,'source_pairs':ep['test'],'program':ep['program_solution']}}

def intermediate(g,settings):
    p=parse(g);chosen=select(p,setting(settings))
    return {'cross_centers':[list(c) for c in sorted(p['centers'])],
            'cross_bearing_components':[{'size':len(s),'bbox':list(bbox(s)),'cross_centers':[list(c) for c in sorted(s&p['centers'])]} for s in p['bearing']],
            'selected_component_bboxes':[list(bbox(s)) for s in chosen]}

def counterfactual_program(settings):return rival_program(settings,'smallest_cross_component')

def dependency():
    return {'step_a':'Detect all plus centers, segment yellow four-connected components and rank only cross-bearing components by occupied-cell count.',
            'intermediate':'Selected component identity and size, plus the exact centers belonging to that component.',
            'step_b':'Paint the union of five-cell plus stencils at those selected centers cyan, simultaneously from the original input.',
            'why_b_depends_on_a':'A larger unrelated component must be ignored and the winning mask depends on global cross-bearing area comparison; substituting the smallest bearing component changes which crosses are rendered.'}

# Standalone ordinary entry point; native functions above remain source provenance.
TASK_ID=GENERATOR_ID='public_eval_1818057f'
RULE_TASK_ID='ee_1818057f'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
MIN_TRAIN=2
MAX_TRAIN=6

def generate(seed,sample_index=0,difficulty=None):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    return _scene(seed,f'ordinary:{sample_index}',stress=difficulty=='hard' or sample_index%4==3)

def rule_mirror(grid):return solve(grid,'all')

# Preserve the ordinary API metadata without a file dependency.
PROGRAM="(rule!\n ;; Find every yellow five-cell orthogonal plus, even inside larger shapes.\n ;; Diagonal cells and extensions beyond the four arms do not disqualify it.\n ;; All detections use the original grid, so overlapping crosses are simultaneous.\n ;; Recolor the union of their center/arm cells cyan; leave all other cells alone.\n (lambda (g)\n  (let ()\n   (define selection-mode 0)\n   (define detection-mode 0)\n   (define painting-mode 0)\n   (define use-eight #f)\n   (define plus '((0 0) (-1 0) (1 0) (0 -1) (0 1)))\n   (define diagonals '((0 0) (-1 -1) (-1 1) (1 -1) (1 1)))\n   (define stencil (if (= detection-mode 3) diagonals plus))\n   (define comps (filter (lambda (o) (= (obj-color o) 4)) (if use-eight (objects-8 g 2) (objects g 2))))\n   (define centers\n     (for*/list ((r (range 1 (- h 1))) (c (range 1 (- w 1)))\n       #:when (and\n          (for/and ((d stencil)) (= (at g (+ r (first d)) (+ c (second d))) 4))\n          (or (not (= detection-mode 1))\n              (for/and ((d (rest diagonals))) (not (= (at g (+ r (first d)) (+ c (second d))) 4))))\n          (or (not (= detection-mode 2))\n              (for/or ((o comps)) (and (= (obj-size o) 5) (member (list r c) (obj-cells o)))))))\n       (list r c)))\n   (define bearing (filter (lambda (o) (for/or ((p centers)) (member p (obj-cells o)))) comps))\n   (define (cross-count o) (length (filter (lambda (p) (member p (obj-cells o))) centers)))\n   (define chosen\n     (cond ((and (= selection-mode 7) (not (null? comps))) (list (pick-max comps obj-size)))\n           ((null? bearing) '())\n           ((= selection-mode 0) bearing)\n           ((= selection-mode 1) (list (pick-max bearing obj-size)))\n           ((= selection-mode 2) (list (pick-min bearing obj-size)))\n           ((= selection-mode 3) (list (first bearing)))\n           ((= selection-mode 4) (list (last bearing)))\n           ((= selection-mode 5) (list (pick-max bearing (lambda (o) (* (obj-h o) (obj-w o))))))\n           ((= selection-mode 6) (list (pick-max bearing cross-count)))\n           ((= selection-mode 8) (list (pick-max bearing obj-w)))\n           ((= selection-mode 9) (list (pick-max bearing obj-h)))\n           (else '())))\n   (define active (filter (lambda (p) (for/or ((o chosen)) (member p (obj-cells o)))) centers))\n   (define paint-offsets (cond ((= painting-mode 1) '((0 0)))\n                               ((= painting-mode 2) '((0 0) (0 -1) (0 1)))\n                               ((= painting-mode 3) '((0 0) (-1 0) (1 0)))\n                               (else stencil)))\n   (for/fold ((out g)) ((p active))\n     (if (and (= painting-mode 4)\n              (not (for/and ((d plus)) (= (at out (+ (first p) (first d)) (+ (second p) (second d))) 4))))\n       out\n       (recolor-cells out (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) paint-offsets) 8))))))\n"
