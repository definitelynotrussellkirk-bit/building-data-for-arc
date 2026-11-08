"""Native mirrored-strip family; Python claims require independent Racket checks."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import random

HOME=Path(__file__).resolve().parent
MODES=('all_components','largest_mirrored')
POLICIES=('canonical','largest','before','before_then_after','all_max','last_tie','smallest',
          'first','last','bbox','width','height','bottommost','eight','stack_then_largest',
          'canonical_copies','canonical_mirror_right','canonical_repeat','canonical_reverse_phase','canonical_all_flip',
          'largest_copies','largest_mirror_right','largest_repeat','largest_reverse_phase','largest_all_flip')


def _int(name,value,lo,hi):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an integer in [{lo},{hi}]')


def _settings(settings):
    if not isinstance(settings,dict) or set(settings)!={'mode'} or settings['mode'] not in MODES:
        raise ValueError('settings must contain exactly one supported mode')
    return settings['mode']


def _grid(g):
    if (not isinstance(g,list) or not 1<=len(g)<=10 or not isinstance(g[0],list) or not 1<=len(g[0])<=15 or
        any(not isinstance(row,list) or len(row)!=len(g[0]) for row in g) or
        any(type(v) is not int or not 0<=v<=9 for row in g for v in row)):
        raise ValueError('input must be a rectangular integer grid <=10x15, so the answer fits 30x30')


def components(g,eight=False):
    seen=set();groups=[]
    offsets=([(r,c) for r in (-1,0,1) for c in (-1,0,1) if (r,c)!=(0,0)] if eight else [(1,0),(-1,0),(0,1),(0,-1)])
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if not color or (r,c) in seen:continue
            group=[];stack=[(r,c)];seen.add((r,c))
            while stack:
                rr,cc=stack.pop();group.append((rr,cc))
                for dr,dc in offsets:
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<len(g) and 0<=nc<len(row) and (nr,nc) not in seen and g[nr][nc]==color:
                        seen.add((nr,nc));stack.append((nr,nc))
            groups.append(group)
    return groups


def mirror(g,kind='mirror_left'):
    if kind=='mirror_left':return [row[::-1]+row[:] for row in g]
    if kind=='mirror_right':return [row[:]+row[::-1] for row in g]
    if kind=='copies':return [row[:]+row[:] for row in g]
    raise ValueError('unknown horizontal rule')


def stack(g,kind='alternating'):
    if kind=='alternating':out=g[::-1]+g+g[::-1]
    elif kind=='repeat':out=g*3
    elif kind=='reverse_phase':out=g+g[::-1]+g
    elif kind=='all_flip':out=g[::-1]*3
    else:raise ValueError('unknown vertical rule')
    return deepcopy(out)


def mask(g,selector='largest'):
    groups=components(g,eight=selector=='eight')
    if not groups:return deepcopy(g)
    def span(cells,axis):return max(x[axis] for x in cells)-min(x[axis] for x in cells)+1
    score={'bbox':lambda x:span(x,0)*span(x,1),'width':lambda x:span(x,1),'height':lambda x:span(x,0),'bottommost':lambda x:max(r for r,c in x)}.get(selector,len)
    if selector=='first':chosen=groups[0]
    elif selector=='last':chosen=groups[-1]
    elif selector=='smallest':chosen=min(groups,key=len)
    elif selector=='all_max':chosen=[cell for group in groups if len(group)==max(map(len,groups)) for cell in group]
    elif selector=='last_tie':chosen=max(reversed(groups),key=len)
    else:chosen=max(groups,key=score)
    keep=set(chosen)
    return [[v if (r,c) in keep else 0 for c,v in enumerate(row)] for r,row in enumerate(g)]


def predict(g,policy):
    if policy not in POLICIES:raise ValueError('unknown policy')
    if policy=='canonical':return stack(mirror(g))
    if policy=='before':return stack(mirror(mask(g)))
    if policy=='before_then_after':return stack(mask(mirror(mask(g))))
    if policy=='stack_then_largest':return mask(stack(mirror(g)))
    for prefix in ('canonical_','largest_'):
        if policy.startswith(prefix):
            kind=policy.removeprefix(prefix)
            horizontal=kind if kind in ('copies','mirror_right') else 'mirror_left'
            vertical=kind if kind in ('repeat','reverse_phase','all_flip') else 'alternating'
            wide=mirror(g,horizontal)
            if prefix=='largest_':wide=mask(wide)
            return stack(wide,vertical)
    return stack(mask(mirror(g),policy))


def solve(g,mode):
    _grid(g)
    if mode not in MODES:raise ValueError('unsupported mode')
    return predict(g,'canonical' if mode=='all_components' else 'largest')


def program(settings):
    mode=_settings(settings)
    return (HOME/('canonical.rkt' if mode=='all_components' else 'largest_mirrored.rkt')).read_text()


def _lesson(seed,index):
    rng=random.Random(f'mirror/lesson/{seed}/{index}')
    color=rng.randint(1,9);kind=index%3
    if kind==2:
        h,w=rng.randint(9,10),rng.randint(10,15)
        g=[[0]*w for _ in range(h)]
        # A 5-cell L has larger bbox than the 6-cell rectangle. Two diagonal
        # singletons merge with the L under 8-, but not 4-, connectivity.
        dc=rng.randrange(w-8)
        cells=[(0,1+dc),(1,2+dc),(2,3+dc),(3,3+dc),(4,3+dc),(4,4+dc),(4,5+dc)]
        cells += [(r,c+dc) for r in (6,7) for c in (4,5,6)]
        for r,c in cells:g[r][c]=color
        # Put this winner above the other objects: bottommost is not largest.
        return g[::-1]
    h,w=rng.randint(7,10),rng.randint(8,15)
    g=[[0]*w for _ in range(h)]
    if kind==0:
        # A 3-cell seam component becomes 6. The larger off-seam L stays
        # separate in the two mirror halves; ties must select only one copy.
        seam_start=rng.randint(0,1)
        for r in range(seam_start,seam_start+3):g[r][0]=color
        length=rng.randint(5,min(7,w-2));start=rng.randint(2,w-length)
        for c in range(start,start+length):g[h-1][c]=color
        for r in (h-3,h-2):g[r][start]=color
    else:
        # Original rank: off-seam 5 > seam 3. Mirrored rank: seam 6 > 5.
        for r in range(h-3,h):g[r][0]=color
        c=rng.randint(3,w-3);r0=rng.randint(0,h-6)
        cells=[(r0,c),(r0+1,c),(r0+2,c),(r0+2,c+1),(r0+2,c+2)]
        for r,cc in cells:g[r][cc]=color
    return g


def _query(seed,index):
    rng=random.Random(f'mirror/query/{seed}/{index}');color=rng.randint(1,9)
    h,w=((3,2),(5,7),(8,12),(10,15))[index]
    if index==3:
        # A connected perimeter is the selected component. The mirror seam
        # joins its copies. Separated interior islands remain distractors.
        g=[[color if r in (0,h-1) or c in (0,w-1) else 0 for c in range(w)] for r in range(h)]
        for r in (2,4,6):
            for c in range(2,w-2):
                if rng.random()<0.65:g[r][c]=color
        return g
    for _ in range(64):
        g=[[color if rng.random()<0.36 else 0 for _ in range(w)] for _ in range(h)]
        if (0<sum(v!=0 for row in g for v in row)<h*w and
            any(row!=row[::-1] for row in g) and g!=g[::-1]):
            return g
    raise ValueError('bounded query construction exhausted')


def generate(seed,settings,demos,queries):
    mode=_settings(settings);_int('seed',seed,0,2**63-1);_int('demos',demos,3,6);_int('queries',queries,1,4)
    train=[_lesson(seed,i) for i in range(demos)];test=[_query(seed,i) for i in range(4)]
    if len({repr(g) for g in train+test})!=demos+4:raise ValueError('duplicate episode input')
    return {'train':[{'input':g,'output':solve(g,mode)} for g in train],
            'test':[{'input':g,'output':solve(g,mode)} for g in test[:queries]],'program_solution':program(settings)}


def teaching_check(e):
    survivors=[];failures=[]
    for policy in POLICIES:
        if all(predict(pair['input'],policy)==pair['output'] for pair in e['train']):
            survivors.append(policy)
            bad=[i for i,pair in enumerate(e['test']) if predict(pair['input'],policy)!=pair['output']]
            if bad:failures.append({'policy':policy,'queries':bad})
    return {'policies':len(POLICIES),'survivors':survivors,'failures':failures}


def public_turn(e,query_index):
    _int('query_index',query_index,0,len(e['test'])-1)
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in e['train']],
            'test':[{'input':deepcopy(e['test'][query_index]['input'])}]}


def racket_policy(selector='largest',order='after'):
    if selector not in ('largest','eight','bbox','all_max','last_tie','bottommost') or order not in ('after','before','before_then_after','stack_then_largest'):
        raise ValueError('unsupported Racket audit policy')
    objects='objects-8' if selector=='eight' else 'objects'
    score={'bbox':'(lambda (obj) (* (obj-h obj) (obj-w obj)))', 'bottommost':'obj-r2'}.get(selector,'obj-size')
    if selector=='all_max':
        cells='(apply append (map obj-cells (filter (lambda (obj) (= (obj-size obj) (obj-size (pick-max obs obj-size)))) obs)))'
    elif selector=='last_tie':cells='(obj-cells (pick-max (reverse obs) obj-size))'
    else:cells=f'(obj-cells (pick-max obs {score}))'
    expression={'after':'(tile (keep (wide g)))','before':'(tile (wide (keep g)))',
                'before_then_after':'(tile (keep (wide (keep g))))','stack_then_largest':'(keep (tile (wide g)))'}[order]
    return f'''(rule!
  (lambda (g)
    (let ()
      (define (wide x)
        (grid-from-fn (rows x) (* 2 (cols x))
          (lambda (r c) (at x r (if (< c (cols x)) (- (cols x) 1 c) (- c (cols x)))))))
      (define (keep x)
        (let* ((obs ({objects} x 0)))
          (if (null? obs) x
            (let* ((cells {cells}))
              (grid-from-fn (rows x) (cols x)
                (lambda (r c) (if (member (list r c) cells) (at x r c) 0)))))))
      (define (tile x)
        (grid-from-fn (* 3 (rows x)) (cols x)
          (lambda (r c)
            (let* ((block (/ r (rows x)))
                   (rr (mod r (rows x)))
                   (src (if (zero? (mod block 2)) (- (rows x) 1 rr) rr)))
              (at x src c)))))
      {expression})))\n'''
