"""Native border family: recolor, recompute components, then select by contact."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random

TASK='515cca15a0b7'
HERE=Path(__file__).resolve().parent
SETTINGS=('none','gray_to_blue')


def _setting(settings):
    if type(settings) is not dict or set(settings) != {'preprocess'}:
        raise ValueError('settings must contain exactly preprocess')
    x=settings['preprocess']
    if type(x) is not str or x not in SETTINGS: raise ValueError('unsupported preprocess')
    return x


def program(settings):
    setting=_setting(settings); source=(HERE/'canonical.rkt').read_text()
    if setting=='none': return source
    return '(rule! (lambda (g) (let ((g (recolor g 5 1))) '+source[len('(rule! '):-1]+')))'


def counterfactual_program():
    source=(HERE/'canonical.rkt').read_text()
    return '(rule! (lambda (g) (recolor '+source[len('(rule! '):-1]+' 5 1)))'


def _grid(g):
    if type(g) is not list or not g or type(g[0]) is not list or not g[0]:
        raise ValueError('expected nonempty list grid')
    w=len(g[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('expected rectangular exact integer colors')
    return g


def components(g, *, diagonal=False, global_colors=False, ignore_colors=False):
    _grid(g)
    pending={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v}
    result=[]
    deltas=[(-1,0),(1,0),(0,-1),(0,1)]
    if diagonal: deltas += [(-1,-1),(-1,1),(1,-1),(1,1)]
    while pending:
        p=min(pending);color=g[p[0]][p[1]]
        if global_colors:
            cells=sorted(q for q in pending if g[q[0]][q[1]]==color)
            pending.difference_update(cells)
        else:
            pending.remove(p);todo=[p];cells=[]
            while todo:
                r,c=todo.pop();cells.append((r,c))
                for dr,dc in deltas:
                    q=(r+dr,c+dc)
                    if q in pending and (ignore_colors or g[q[0]][q[1]]==color):
                        pending.remove(q);todo.append(q)
        result.append((color,sorted(cells)))
    return result


def recolor(g, color=1):
    return [[color if v==5 else v for v in row] for row in g]


def select(g, *, predicate='both', diagonal=False, global_colors=False, ignore_colors=False, rank=None, suppressed=None):
    h,w=len(g),len(g[0]);selected=[]
    for color,cells in components(g,diagonal=diagonal,global_colors=global_colors,ignore_colors=ignore_colors):
        horizontal=any(r in (0,h-1) for r,c in cells);vertical=any(c in (0,w-1) for r,c in cells)
        keep=horizontal and vertical
        if predicate=='any':keep=horizontal or vertical
        if predicate=='corner':keep=any(r in (0,h-1) and c in (0,w-1) for r,c in cells)
        if predicate=='near':keep=keep and all(min(max(r,c),max(r,w-1-c),max(h-1-r,c),max(h-1-r,w-1-c))<=2 for r,c in cells)
        if suppressed is not None:
            mr=sum(r for r,c in cells)/len(cells);mc=sum(c for r,c in cells)/len(cells)
            quadrant=2*int(mr>=h/2)+int(mc>=w/2)
            keep=keep and quadrant!=suppressed
        if keep:selected.append((color,cells))
    if rank: selected=sorted(selected,key=lambda obj:len(obj[1]),reverse=rank=='largest')[:2]
    out=[[0]*w for _ in range(h)]
    for color,cells in selected:
        for r,c in cells:out[r][c]=g[r][c]
    return out


def predict(g,setting):
    _setting({'preprocess':setting});_grid(g)
    return select(recolor(g) if setting=='gray_to_blue' else g)


def _rng(seed,key):
    return random.Random(int.from_bytes(hashlib.sha256(f'{TASK}:native-v1:{seed}:{key}'.encode()).digest(),'big'))


def _scene(seed,role,index):
    rng=_rng(seed,f'{role}:{index}')
    h,w=(((14,16),(18,20),(22,24),(16,18),(20,22),(26,28))[index] if role=='train'
         else ((15,17),(19,22),(24,27),(30,30))[index])
    q=min((h-2)//2,(w-2)//2);stress=(h,w)==(30,30)
    a=b=q-3 if stress else 0
    if not stress:a=rng.randint(3,q-2);b=rng.randint(3,q-2)
    g=[[0]*w for _ in range(h)]
    corners=[(False,False),(False,True),(True,False),(True,True)]
    _rng(seed,'layout').shuffle(corners)
    shift=index if role=='train' else index+2
    corners=corners[shift%4:]+corners[:shift%4]
    palette=[2,3,4,6,7,8,9];_rng(seed,'palette').shuffle(palette)
    other=palette[index%len(palette)]
    def paint(role_index,points,color):
        bottom,right=corners[role_index]
        for r,c in points:
            rr=h-1-r if bottom else r;cc=w-1-c if right else c
            if g[rr][cc]:raise ValueError('constructive component overlap')
            g[rr][cc]=color
    path=[(r,a) for r in range(b+1)]+[(b,c) for c in range(a-1,-1,-1)]
    cut={(b,a)}
    if index%2:cut.add((1,a))
    paint(0,[p for p in path if p not in cut],1);paint(0,cut,5)
    # A separate literal-corner blue survivor and diagonal-only distractor.
    paint(0,[(0,0),(0,1),(1,0)],1);paint(0,[(b+1,a+1)],1)
    # Foreign-color contact must not be absorbed into the new blue union.
    paint(0,[(2,a+1)],other)
    if stress or index%2:
        body={(r,c) for r in range(1,b+1) for c in range(1,a+1)}|{(0,a),(b,0)}
    else:body=set(path)
    paint(1,body,other)
    failed=[(r,a) for r in range(b+1)]+[(b,c) for c in range(a-1,0,-1)]
    paint(2,[p for p in failed if p!=(b,a)],1);paint(2,[(b,a)],5)
    k=q-3 if stress else rng.randint(2,min(4,q-2))
    paint(3,[(r,c) for r in range(k) for c in range(k)],5)
    # Interior different-color distraction has no border contact.
    g[h//2][w//2]=palette[(index+2)%len(palette)]
    return g


def generate(seed,settings,demos=3,queries=4):
    setting=_setting(settings)
    for name,value,lo,hi in (('seed',seed,0,None),('demos',demos,2,6),('queries',queries,1,4)):
        if type(value) is not int or value<lo or (hi is not None and value>hi):
            raise ValueError(f'{name} outside exact-integer limits')
    train=[_scene(seed,'train',i) for i in range(demos)]
    bank=[_scene(seed,'test',i) for i in range(4)]
    if len({json.dumps(g) for g in train+bank})!=len(train)+4:raise ValueError('constructed duplicate grid')
    def pair(g):return {'input':g,'output':predict(g,setting)}
    return {'train':[pair(g) for g in train],'test':[pair(g) for g in bank[:queries]],
            'program_solution':program(settings),'settings':dict(settings)}


def public_turn(episode,index):
    from reviewer_support import public_challenge_bytes
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
    return json.loads(public_challenge_bytes({'train':episode['train'],'test':[episode['test'][index]]}))


POLICIES=('none','gray_to_blue','wrong_order','identity','recolor_only',
          *[f'{name}_{stage}' for name in ('any','corner','near','diagonal','global','largest_two','smallest_two','ignore_colors') for stage in ('before','after')],
          *[f'wrong_color_{c}' for c in (2,3,4,6,7,8,9)],
          *[f'suppress_{q}_{stage}' for q in range(4) for stage in ('before','after')])


def rival(g,policy):
    if policy in SETTINGS:return predict(g,policy)
    if policy=='wrong_order':return recolor(select(g))
    if policy=='identity':return [row[:] for row in g]
    if policy=='recolor_only':return recolor(g)
    if policy.startswith('wrong_color_'):return select(recolor(g,int(policy.rsplit('_',1)[1])))
    name,stage=policy.rsplit('_',1);work=recolor(g) if stage=='after' else g
    if name in ('any','corner','near'):return select(work,predicate=name)
    if name=='diagonal':return select(work,diagonal=True)
    if name=='global':return select(work,global_colors=True)
    if name=='ignore_colors':return select(work,ignore_colors=True)
    if name in ('largest_two','smallest_two'):return select(work,rank=name.split('_')[0])
    if name.startswith('suppress_'):return select(work,suppressed=int(name.split('_')[1]))
    raise ValueError('unknown policy')


def teaching(episode):
    survivors=[name for name in POLICIES if all(rival(p['input'],name)==p['output'] for p in episode['train'])]
    failures=[{'policy':name,'queries':[i for i,p in enumerate(episode['test']) if rival(p['input'],name)!=p['output']]}
              for name in survivors]
    failures=[x for x in failures if x['queries']]
    return {'policies':len(POLICIES),'survivors':survivors,'query_disagreements':failures,
            'passed':bool(survivors) and not failures}
