"""Native candidate: derive a row-local cue color, then reflect matching sources.

The canonical all-sources rule is preserved byte-for-byte. Alternate settings
select a source color by distance from that row's maroon anchor and copy every
source of the selected color. Python labels are claims for native Racket replay.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
DEFAULT={'copy_policy':'all'}
SETTINGS=tuple({'copy_policy':x} for x in ('all','nearest_color','farthest_color'))
PROFILES=((6,15,3,'core_one'),(8,21,4,'core_two'),(4,7,2,'tiny'),
          (10,14,6,'medium'),(20,11,15,'tall'),(30,30,24,'large_demo'),
          (5,9,3,'small_query'),(12,22,8,'wide_query'),
          (30,17,25,'tall_query'),(30,30,25,'large_query'))


def normalize_settings(settings=None):
    if settings is None:return dict(DEFAULT)
    if type(settings) is not dict or set(settings)-set(DEFAULT):
        raise ValueError('settings must contain only copy_policy')
    out={**DEFAULT,**settings}
    if type(out['copy_policy']) is not str or out['copy_policy'] not in ('all','nearest_color','farthest_color'):
        raise ValueError('copy_policy must be all, nearest_color or farthest_color')
    return out


def _integer(value,name,lo,hi):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')


def analyze_scene(grid):
    if (type(grid) is not list or not 4<=len(grid)<=30
            or type(grid[0]) is not list or not 7<=len(grid[0])<=30
            or any(type(row) is not list or len(row)!=len(grid[0])
                   or any(type(c) is not int or not 0<=c<=9 for c in row) for row in grid)):
        raise ValueError('grid must be rectangular4..30 by7..30 with exact integer colors0..9')
    anchored=[];orphan_nonzero=0;left=right=0
    for r,row in enumerate(grid):
        anchors=[c for c,v in enumerate(row) if v==9]
        if len(anchors)>1:raise ValueError('each row admits at most one maroon anchor')
        if not anchors:
            orphan_nonzero+=sum(v!=0 for v in row)
            continue
        a=anchors[0];sources=[]
        for c,v in enumerate(row):
            if v in (0,9):continue
            target=2*a-c
            if not 0<=target<len(row) or row[target]!=0:
                raise ValueError('every reflected target must be in bounds and empty')
            sources.append({'column':c,'color':v,'distance':abs(c-a),'target':target})
            left+=c<a;right+=c>a
        if not sources:raise ValueError('anchored rows need a source')
        if len({s['distance'] for s in sources})!=len(sources):
            raise ValueError('source distances must be unique within a row')
        near=min(sources,key=lambda s:s['distance'])
        far=max(sources,key=lambda s:s['distance'])
        anchored.append({'row':r,'anchor':a,'sources':sources,
                         'nearest_column':near['column'],'nearest_color':near['color'],
                         'farthest_column':far['column'],'farthest_color':far['color']})
    if not 2<=len(anchored)<len(grid):
        raise ValueError('at least two anchored rows and one orphan row are required')
    if not left or not right:raise ValueError('sources must occur on both sides across the grid')
    return {'height':len(grid),'width':len(grid[0]),'anchored':anchored,
            'anchor_count':len(anchored),'orphan_nonzero':orphan_nonzero,
            'source_count':sum(len(r['sources']) for r in anchored),
            'left_sources':left,'right_sources':right}


def python_apply(grid,settings=None):
    policy=normalize_settings(settings)['copy_policy']
    info=analyze_scene(grid)
    out=deepcopy(grid)
    for row in info['anchored']:
        chosen=None if policy=='all' else row[policy]
        for s in row['sources']:
            if chosen is None or s['color']==chosen:
                out[row['row']][s['target']]=s['color']
    return out


def program(settings=None):
    policy=normalize_settings(settings)['copy_policy']
    if policy=='all':return (HERE/'canonical.rkt').read_text()
    choose='argmin' if policy=='nearest_color' else 'argmax'
    return f"""(rule! (lambda (g)
  (for/fold ((out g)) ((r (in-range (rows g))))
    (let ((anchors (filter (lambda (c) (= (at g r c) 9)) (range (cols g)))))
      (if (empty? anchors) out
          (let* ((a (first anchors))
                 (sources (filter (lambda (c) (not (member? (at g r c) (list 0 9))))
                                  (range (cols g))))
                 (cue ({choose} (lambda (c) (abs (- c a))) sources))
                 (selected-color (at g r cue)))
            (for/fold ((acc out)) ((c (in-list sources)))
              (let ((v (at g r c)) (mc (- (* 2 a) c)))
                (if (and (= v selected-color) (in-bounds? r mc (rows g) (cols g)))
                    (set-cell acc r mc v) acc)))))))))"""


def _rng(seed,slot):
    key=hashlib.sha256(f'71f7823f30a3-native-v1:{seed}:{slot}'.encode()).digest()
    return random.Random(int.from_bytes(key,'big'))


def _row(grid,r,anchor,distances,labels,index,*,edge_side=None):
    grid[r][anchor]=9
    for j,(d,color) in enumerate(zip(distances,labels)):
        side=-1 if (j+index)%2==0 else 1
        if edge_side is not None and j==len(distances)-1:side=edge_side
        grid[r][anchor+side*d]=color


def _orphans(grid,colors,rng):
    rows=[r for r,row in enumerate(grid) if 9 not in row]
    grid[rows[0]][0]=colors[0]
    grid[rows[0]][-1]=colors[1]
    for r in rows[1:]:
        if rng.random()<.6:
            for c in rng.sample(range(len(grid[0])),min(3,len(grid[0]))):
                grid[r][c]=rng.choice(colors)


def _core(which,colors):
    h,w,_,_=PROFILES[which]
    g=[[0]*w for _ in range(h)]
    rows=(0,2,5) if which==0 else (0,2,5,7)
    anchors=(6,8,7) if which==0 else (9,11,10,8)
    for i,(r,anchor) in enumerate(zip(rows,anchors)):
        a,b,c=colors[i%3:]+colors[:i%3]
        if which==0:
            distances=[1,2,3,4,5,6];labels=[a,b,c,a,b,c]
        elif i==0:
            distances=[2,3,4,5,6,7,8];labels=[a,a,b,b,b,c,c]
        elif i==1:
            distances=[1,2,4,5,7,8];labels=[a,a,a,b,c,c]
        elif i==2:
            distances=[2,3,4,5,7,8];labels=[a,b,b,c,c,c]
        else:
            distances=[1,7];labels=[a,a]
        _row(g,r,anchor,distances,labels,i)
    return g


def _general(h,w,count,kind,colors,rng):
    g=[[0]*w for _ in range(h)]
    anchor_rows=sorted([0,h-1]+rng.sample(range(1,h-1),count-2))
    for i,r in enumerate(anchor_rows):
        anchor=((w-1)//2 if i==0 else w//2 if i==count-1
                else rng.randint(max(3,w//2-3),min(w-4,w//2+3)))
        span=min(anchor,w-1-anchor)
        k=(span-rng.randrange(3) if kind.startswith('large')
           else max(3,span-rng.randrange(2)))
        distances=sorted(rng.sample(range(1,span+1),k))
        if i in (0,count-1) and span not in distances:
            distances[-1]=span
        a,b,c=colors[i%3:]+colors[:i%3]
        if k==3:labels=[a,a,b]
        else:
            labels=[(a,b,c)[j%3] for j in range(k)]
            labels[0]=a;labels[1]=b;labels[-2]=a;labels[-1]=b
        _row(g,r,anchor,distances,labels,i,
             edge_side=-1 if i==0 else 1 if i==count-1 else None)
    return g


def _scene(seed,slot):
    rng=_rng(seed,slot)
    colors=rng.sample(range(1,9),3)
    h,w,count,kind=PROFILES[slot]
    grid=_core(slot,colors) if slot<2 else _general(h,w,count,kind,colors,rng)
    _orphans(grid,colors,rng)
    if rng.getrandbits(1):grid=[row[::-1] for row in grid]
    if rng.getrandbits(1):grid=grid[::-1]
    analyze_scene(grid)
    return grid


def generate(seed,settings=None,demos=3,queries=4):
    _integer(seed,'seed',0,2**63-1)
    _integer(demos,'demos',2,6)
    _integer(queries,'queries',1,4)
    chosen=normalize_settings(settings)
    bank=[_scene(seed,i) for i in range(10)]
    if len({repr(g) for g in bank})!=10:
        raise RuntimeError('constructive bank unexpectedly contains duplicate inputs')
    def pair(g):return {'input':deepcopy(g),'output':python_apply(g,chosen)}
    return {'train':[pair(g) for g in bank[:demos]],
            'test':[pair(g) for g in bank[6:6+queries]],
            'program_solution':program(chosen),'settings':chosen,
            'meta':{'seed':seed,'status':'proposed_owner_pending','training_admitted':False,
                    'candidate_attempts':10,'rejections':0,
                    'label_basis':'Python claims; protected Racket required',
                    'input_rng_independent_of_settings_and_counts':True,
                    'height_range':[4,30],'width_range':[7,30],
                    'production_height_range':[4,10],'production_width_range':[7,15]}}
