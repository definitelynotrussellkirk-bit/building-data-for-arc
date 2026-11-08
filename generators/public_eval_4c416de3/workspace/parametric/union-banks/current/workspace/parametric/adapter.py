"""Matched-input corner glyph family; all resources stay in this directory."""
from __future__ import annotations
from pathlib import Path
import copy
import hashlib
import importlib.util
import random
import sys
from puzzle_generators.base import gen_ctx

BASE=Path(__file__).resolve().parent
TASK='public_eval_4c416de3'
VERSION='1.0.1'


def local(name):
    path=BASE/(name+'.py');key='_corner_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path)
        module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return sys.modules[key]

model=local('model')


def setting(settings):
    if type(settings) is not dict or set(settings)!={'copy_extent'} or settings['copy_extent'] not in ('full','outside'):
        raise ValueError('settings must be exactly copy_extent=full|outside')
    return settings['copy_extent']


def program(settings):
    return (BASE/('canonical.rkt' if setting(settings)=='full' else 'outside.rkt')).read_text()


MOTIFS=(
    ((-1,0),(0,-1),(0,0),(1,1),(2,1),(2,2)),
    ((-1,-1),(-1,0),(0,-1),(0,1),(1,0),(1,1),(1,2)),
    ((-1,-1),(-1,0),(0,-1),(0,0),(1,1),(2,2)),
    ((-1,0),(0,-1),(0,0),(1,1),(1,2),(2,1)),
    ((-1,-1),(-1,0),(0,0),(1,1),(1,2),(2,2)),
    ((-1,0),(0,-1),(0,0),(1,0),(1,1),(2,1)),
)


def sample_input(seed,index):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:
        raise ValueError('seed and index must be nonnegative exact integers')
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    rng=ctx.draw_rng('corner-scene');stress=index==103
    h=30 if stress else rng.randrange(24,31);w=30 if stress else rng.randrange(24,31)
    palette=list(range(1,10));rng.shuffle(palette);bg=palette.pop()
    g=[[bg]*w for _ in range(h)]
    span1=rng.randrange(7,10);span2=rng.randrange(7,10)
    if stress:
        frames=[(0,0,9,10),(0,19,10,29),(19,0,29,9),(19,19,29,29)]
    elif index==1:
        # Four frames make cross-frame global-color contamination visible even
        # when the chosen rule copies only exterior coordinates.
        frames=[(0,0,7,7),(0,w-8,7,w-1),(h-8,0,h-1,7),(h-8,w-8,h-1,w-1)]
    elif index==100:
        frames=[(2,2,h-3,w-3)]
    else:
        margin=0 if index%2==0 else 2
        bottom=min(margin+span1,h//2-3);right=min(margin+span2,w//2-3)
        frames=[(margin,margin,bottom,right),
                (max(h-span2-3,bottom+5),max(w-span1-3,right+5),h-1,w-1)]
        if index==102:
            # The last rectangle extends off canvas: only its top-left corner is visible.
            frames[-1]=(h-9,w-9,h+3,w+4)
    def put(r,c,v):
        if 0<=r<h and 0<=c<w:g[r][c]=v
    corners=[]
    for top,left,bottom,right in frames:
        for c in range(left,right+1):put(top,c,0);put(bottom,c,0)
        for r in range(top,bottom+1):put(r,left,0);put(r,right,0)
        for r,c,sr,sc in ((top,left,1,1),(top,right,1,-1),(bottom,left,-1,1),(bottom,right,-1,-1)):
            if 0<=r<h and 0<=c<w:corners.append((r,c,sr,sc))
    motif=list(MOTIFS[4 if index==0 else 1] if index in (0,1) else rng.choice(MOTIFS))
    # A random transposition varies glyph handedness without changing the rule.
    if rng.randrange(2):motif=[(b,a)for a,b in motif]
    source_candidates=[i for i,(r,c,sr,sc)in enumerate(corners)
        if all(0<=r+sr*a<h and 0<=c+sc*b<w for a,b in motif)]
    source=3 if index in (0,1) else rng.choice(source_candidates)
    source_color=palette[0]
    for i,(r,c,sr,sc)in enumerate(corners):
        color=palette[i%4]
        if i in (source,source^3):color=source_color
        # Repeated colors across unrelated corners block global-color grouping.
        if i==source:points=motif
        else:
            inside=[p for p in motif if p[0]>0 and p[1]>0]
            points=[(1,1)] if index in (0,1) else [rng.choice(inside)]
        for a,b in points:put(r+sr*a,c+sc*b,color)
    d=model.analyze(g)
    if set(d['motif'])!=set(motif) or len(d['groups'])!=len(corners):
        raise RuntimeError('Constructed corner grammar is ambiguous')
    return g


def generate(seed,settings,demos,queries):
    mode=setting(settings)
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(index):
        g=sample_input(seed,index);return {'input':g,'output':model.solve(g,mode)}
    train=[pair(i)for i in range(demos)];bank=[pair(100+i)for i in range(4)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'program_solution':program(settings),
            'settings':copy.deepcopy(settings),'seed':seed,'private':{'query_bank':bank}}


def public_view(episode,turn=0,presentation_seed=0):
    if type(turn) is not int or not 0<=turn<4:raise ValueError('turn must be 0..3')
    if type(presentation_seed) is not int:raise ValueError('presentation_seed must be an integer')
    bank=episode['private']['query_bank']
    if len(bank)!=4:raise ValueError('Four private queries required')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])}for p in episode['train']]
    return {'train':train,'test':[{'input':copy.deepcopy(bank[order[turn]]['input'])}]}
