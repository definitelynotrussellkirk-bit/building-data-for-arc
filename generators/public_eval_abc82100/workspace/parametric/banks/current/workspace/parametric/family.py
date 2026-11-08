"""Keyed cyan-template substitution, with explicit shape/anchor segmentation.

Each template has a two-cell handle: outer source color, inner paint color.
Its boundary position in line with the handle is the stamp anchor (possibly a
zero cell). Markers are read simultaneously; template/handle cells are erased.
Touching thin templates are partitioned by maximal cyan rays from their handles.
"""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
BASE=Path(__file__).resolve().parent
DIRECTIONS=((-1,0),(0,1),(1,0),(0,-1))
SETTINGS=('stamp','mark_overlap')


def validate_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('Expected a rectangular integer-color grid within 30x30')


def components8(cells):
    unseen=set(cells);result=[]
    while unseen:
        p=min(unseen);unseen.remove(p);component={p};todo=[p]
        while todo:
            r,c=todo.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    q=r+dr,c+dc
                    if q in unseen:unseen.remove(q);component.add(q);todo.append(q)
        result.append(component)
    return result


def analyze(g):
    validate_grid(g);h,w=len(g),len(g[0])
    def at(p):
        r,c=p;return g[r][c] if 0<=r<h and 0<=c<w else 0
    def handle(source,target,anchor,cells):
        s,t=at(source),at(target)
        if s not in (0,8) and t not in (0,8) and s!=t:
            return {'source':s,'color':t,'handle':[source,target],'anchor':anchor,
                    'cells':sorted(cells),'offsets':sorted((r-anchor[0],c-anchor[1]) for r,c in cells)}
        return None
    templates=[]
    cyan={(r,c) for r in range(h) for c in range(w) if g[r][c]==8}
    for comp in components8(cyan):
        r0,r1=min(r for r,c in comp),max(r for r,c in comp)
        c0,c1=min(c for r,c in comp),max(c for r,c in comp)
        candidates=[]
        for dr,dc in DIRECTIONS: # inward direction from handle to template
            if dr:
                anchors=[(r0 if dr==1 else r1,c) for c in range(c0,c1+1)]
            else:
                anchors=[(r,c0 if dc==1 else c1) for r in range(r0,r1+1)]
            for a in anchors:
                target=(a[0]-dr,a[1]-dc);source=(a[0]-2*dr,a[1]-2*dc)
                candidate=handle(source,target,a,comp)
                if candidate:candidates.append(candidate)
        if len(candidates)==1:
            templates+=candidates;continue
        if candidates:
            raise ValueError('Ambiguous multiple handles on one cyan template')
        # A connected cyan region may contain touching parallel line templates.
        rays=[]
        for a in sorted(comp):
            for dr,dc in DIRECTIONS:
                t=a[0]-dr,a[1]-dc;s=a[0]-2*dr,a[1]-2*dc
                cells=[];p=a
                while p in comp:
                    cells.append(p);p=p[0]+dr,p[1]+dc
                candidate=handle(s,t,a,cells)
                if candidate:rays.append(candidate)
        cover=Counter(p for ray in rays for p in ray['cells'])
        if set(cover)!=comp or any(n!=1 for n in cover.values()):
            raise ValueError('Unkeyed/ambiguous cyan region; no exact thin-template partition')
        templates+=rays
    if not templates:raise ValueError('No keyed cyan templates')
    if len({t['source'] for t in templates})!=len(templates):
        raise ValueError('A source color must identify exactly one template')
    removed=cyan|{p for t in templates for p in t['handle']}
    return {'templates':templates,'removed':removed}


def expand(g, *, bbox_counts=False, reverse_keys=False, no_clip=False, center_anchor=False, box_shapes=False, only_first=False):
    info=analyze(g);h,w=len(g),len(g[0])
    templates=copy.deepcopy(info['templates'])
    if only_first:templates=templates[:1]
    if reverse_keys:
        for t in templates:t['source'],t['color']=t['color'],t['source']
    source_colors={t['source'] for t in templates}
    out=[[0 if (r,c) in info['removed'] or v in source_colors else v for c,v in enumerate(row)] for r,row in enumerate(g)]
    coverage=Counter();instances=[]
    for t in templates:
        offsets=t['offsets']
        if center_anchor:
            rs=[r for r,c in t['cells']];cs=[c for r,c in t['cells']]
            mid=((min(rs)+max(rs))//2,(min(cs)+max(cs))//2)
            offsets=[(r-mid[0],c-mid[1]) for r,c in t['cells']]
        if box_shapes:
            rr=[r for r,c in offsets];cc=[c for r,c in offsets]
            offsets=[(r,c) for r in range(min(rr),max(rr)+1) for c in range(min(cc),max(cc)+1)]
        count_offsets=offsets
        if bbox_counts:
            rr=[r for r,c in offsets];cc=[c for r,c in offsets]
            count_offsets=[(r,c) for r in range(min(rr),max(rr)+1) for c in range(min(cc),max(cc)+1)]
        for r,row in enumerate(g):
            for c,v in enumerate(row):
                if v!=t['source'] or (r,c) in info['removed']:continue
                raw=[(r+dr,c+dc) for dr,dc in offsets]
                if no_clip and any(not (0<=a<h and 0<=b<w) for a,b in raw):continue
                cells=[(a,b) for a,b in raw if 0<=a<h and 0<=b<w]
                instances.append({'source':[r,c],'color':t['color'],'cells':cells})
                for a,b in cells:out[a][b]=t['color']
                for dr,dc in count_offsets:
                    if 0<=r+dr<h and 0<=c+dc<w:coverage[r+dr,c+dc]+=1
    return out,coverage,instances


def solve(g,finish='stamp'):
    if finish not in SETTINGS:raise ValueError('Undeclared finish')
    out,coverage,_=expand(g)
    if finish=='mark_overlap':
        for (r,c),n in coverage.items():
            if n>=2:out[r][c]=9
    return out


def rng(seed,stream):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}/{stream}'.encode()).digest(),'big'))


def transform(g,k):
    out=[row[::-1] if k>=4 else row[:] for row in g]
    for _ in range(k%4):out=[list(row) for row in zip(*out[::-1])]
    return out


def touching_scene(seed,index,n):
    prng=rng(seed,f'touching/{index}');s0,t0,s1,t1=prng.sample([1,2,3,4,5,6,7],4)
    g=[[0]*n for _ in range(n)]
    # The two cyan columns touch through most of their lengths but are separate
    # opposite-pointing stencils. The two unused end keys are real data markers.
    g[0][0]=g[0][1]=s0;g[1][1]=t0
    g[n-1][0]=g[n-1][1]=s1;g[n-2][0]=t1
    for r in range(1,n-2):g[r][0]=8
    for r in range(2,n-1):g[r][1]=8
    for j,c in enumerate(range(4,n,3)):
        s=s0 if j%2==0 else s1
        if s==s0:rr=[prng.randint(3,6),prng.randint(n//2,n//2+2)]
        else:rr=[prng.randint(n//2-2,n//2),prng.randint(n-6,n-3)]
        for r in rr:g[r][c]=s
    unused=next(v for v in range(1,8) if v not in (s0,t0,s1,t1))
    g[n//2][3]=unused
    return transform(g,prng.randrange(8))


def scene(seed,index,n,*,touching=False):
    if touching:return touching_scene(seed,index,n)
    prng=rng(seed,f'regular/{index}');k=3 if n==30 else 2
    palette=prng.sample([1,2,3,4,5,6,7],2*k)
    sources=palette[:k];targets=palette[k:]
    if seed%3==0 and k==2:targets=sources[::-1]  # simultaneous reciprocal substitution
    shapes=[[(0,1),(1,0),(1,2),(2,1)],
            [(0,1),(1,0),(1,1),(2,1)],
            [(0,0),(1,0),(2,0)]]
    g=[[0]*n for _ in range(n)];desc=[]
    for i in range(k):
        shape=shapes[i];sh=max(r for r,c in shape)+1;sw=max(c for r,c in shape)+1
        r0=3;c0=(n*i)//k+(n//k-sw)//2
        for r,c in shape:g[r0+r][c0+c]=8
        dr,dc=prng.choice(DIRECTIONS)
        if dr:a=(r0 if dr==1 else r0+sh-1,c0+(sw-1)//2)
        else:a=(r0+(sh-1)//2,c0 if dc==1 else c0+sw-1)
        t=a[0]-dr,a[1]-dc;s=a[0]-2*dr,a[1]-2*dc
        assert 0<=s[0]<n and 0<=s[1]<n and g[s[0]][s[1]]==0 and g[t[0]][t[1]]==0
        g[s[0]][s[1]]=sources[i];g[t[0]][t[1]]=targets[i]
        offsets=[(r0+r-a[0],c0+c-a[1]) for r,c in shape]
        desc.append({'source':sources[i],'color':targets[i],'offsets':offsets})
    painted=set();markers=set()
    for i,d in enumerate(desc):
        top=([10,17,24] if k==3 else [10,n-5])[i]
        left=prng.randint(3,n-8)
        dr0=min(r for r,c in d['offsets']);dc0=min(c for r,c in d['offsets'])
        anchor=(top-dr0,left-dc0)
        anchors=[anchor,(anchor[0],anchor[1]+2)]
        if i==0:
            edge=0 if dc0<0 else n-1
            anchors.append((anchor[0],edge))
        else:
            anchors.append((anchor[0],prng.choice([2,n-3])))
        for r,c in anchors:
            if (r,c) in markers:continue
            assert 0<=r<n and 0<=c<n and g[r][c]==0
            g[r][c]=d['source'];markers.add((r,c))
            painted.update((r+dr,c+dc) for dr,dc in d['offsets'] if 0<=r+dr<n and 0<=c+dc<n)
    unknown=next(v for v in range(1,8) if v not in sources+targets)
    candidates=[(r,c) for r in range(9,n) for c in range(n) if g[r][c]==0 and (r,c) not in painted]
    for r,c in prng.sample(candidates,min(5,len(candidates))):g[r][c]=unknown
    # A whole-scene dihedral transform changes handle direction and clipping
    # geometry while preserving the explicit template semantics.
    return transform(g,prng.randrange(8))


def check_settings(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in SETTINGS:
        raise ValueError('Exactly one declared finish setting is required')
    return settings['finish']


def program(settings):
    finish=check_settings(settings)
    return (BASE/('canonical.rkt' if finish=='stamp' else 'mark_overlap.rkt')).read_text()


def generate(seed,settings,demos=2,queries=4):
    finish=check_settings(settings)
    if type(seed) is not int or seed<0 or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('Nonnegative integer seed, 2..6 demos and 1..4 queries required')
    sizes=[22,24,26,28,23,25]
    train_in=[scene(seed,f'demo/{i}',sizes[i],touching=i%2==1) for i in range(demos)]
    bank=[scene(seed,f'query/{i}',n,touching=i%2==1) for i,n in enumerate([30,30,24,28])]
    order=list(range(4));rng(seed,'presentation').shuffle(order)
    pair=lambda g:{'input':g,'output':solve(g,finish)}
    return {'train':[pair(g) for g in train_in],'test':[pair(bank[i]) for i in order[:queries]],
            'program_solution':program(settings),'private':{'source_indices':order[:queries],'settings':copy.deepcopy(settings),'seed':seed}}


def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('No such current query')
    return copy.deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                          'test':[{'input':episode['test'][index]['input']}]})


def rival_names(finish):
    return ['other_setting','reverse_keys','bounding_box','center_anchor','drop_clipped','first_template']+(['mark_all'] if finish=='mark_overlap' else [])


def rival(g,finish,name):
    if name=='other_setting':return solve(g,'mark_overlap' if finish=='stamp' else 'stamp')
    flags={'reverse_keys':{'reverse_keys':True},'bounding_box':{'box_shapes':True},
           'center_anchor':{'center_anchor':True},'drop_clipped':{'no_clip':True},'first_template':{'only_first':True},'mark_all':{}}
    if name not in flags:raise ValueError(name)
    out,coverage,_=expand(g,**flags[name])
    if finish=='mark_overlap':
        for (r,c),count in coverage.items():
            if count>=(1 if name=='mark_all' else 2):out[r][c]=9
    return out


def rival_program(finish,name):
    if name=='other_setting':return program({'finish':'mark_overlap' if finish=='stamp' else 'stamp'})
    source=(BASE/'canonical.rkt').read_text()
    if name=='reverse_keys':
        source=source.replace('(list (value (plus a d -2)) (value (plus a d -1))',
                              '(list (value (plus a d -1)) (value (plus a d -2))')
    elif name=='bounding_box':
        source=source.replace('(list-ref t 5)))','(apply positions-in-rect (bbox-of-cells (list-ref t 5)))))')
    elif name=='center_anchor':
        source=source.replace('(define a (list-ref t 4))',
          '(define bb (bbox-of-cells (list-ref t 5)))\n      (define a (list (quotient (+ (first bb) (third bb)) 2) (quotient (+ (second bb) (fourth bb)) 2)))')
    elif name=='drop_clipped':
        source=source.replace('(filter (lambda (q) (in-bounds? (first q) (second q) (rows g) (cols g)))\n              (map (lambda (d) (plus p d 1)) (offsets t)))',
          "(let ((raw (map (lambda (d) (plus p d 1)) (offsets t)))) (if (andmap (lambda (q) (in-bounds? (first q) (second q) (rows g) (cols g))) raw) raw '()))")
    elif name=='first_template':
        source=source.replace('(define sources (map first templates))','(define sources (map first (take templates 1)))')
        source=source.replace('(offsets t)))))) templates))','(offsets t)))))) (take templates 1)))')
    elif name!='mark_all':raise ValueError(name)
    if finish=='mark_overlap':
        threshold=1 if name=='mark_all' else 2
        expr=f'(cellmap painted (r c v) (if (>= (count-if (lambda (p) (equal? p (list r c))) footprints) {threshold}) 9 v))'
        source=source.replace(';; RESULT\n    painted))',f';; RESULT\n    {expr}))')
    return source
