"""Native matched-input stencil family, with strict single-turn projection."""
from __future__ import annotations
from pathlib import Path
import copy
import hashlib
import importlib.util
import random
import sys
from puzzle_generators.base import gen_ctx

BASE=Path(__file__).resolve().parent
TASK='public_eval_abc82100'
VERSION='1.0.0'

def local(name):
    path=BASE/(name+'.py'); key='_abc_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path)
        module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return sys.modules[key]

model=local('model')


def setting(settings):
    if type(settings) is not dict or set(settings)!={'stencil_action'} or settings['stencil_action'] not in ('as_drawn','quarter_turn'):
        raise ValueError('settings must name exactly stencil_action=as_drawn|quarter_turn')
    return settings['stencil_action']


def program(settings):
    mode=setting(settings)
    return (BASE/('canonical.rkt' if mode=='as_drawn' else 'quarter_turn.rkt')).read_text()


def rotate_grid(grid, n):
    for _ in range(n): grid=[list(row) for row in zip(*grid[::-1])]
    return grid


def _place(g, sprite, top, left):
    for r,row in enumerate(sprite):
        for c,v in enumerate(row):
            if v: g[top+r][left+c]=v


def _sprite(rng, source, target, k):
    # The entry anchor is deliberately hollow in the first shape. Its support
    # is not a rectangle and its anchor is not the bounding-box corner.
    motifs=[[(0,0),(1,1),(2,0),(2,1),(2,2)],
            [(0,0),(1,0),(2,0),(2,1),(2,2),(3,2)],
            [(0,0),(0,1),(0,2),(1,2),(2,0),(2,1),(2,2)],
            [(0,1),(1,0),(1,1),(1,2),(2,2),(3,1)],
            [(0,0),(0,1),(1,1),(1,2),(2,2),(2,3),(3,3)]]
    cells=motifs[k%len(motifs)]
    sprite=[[0]*7 for _ in range(7)]
    sprite[3][0]=source;sprite[3][1]=target
    for r,c in cells: sprite[2+r][2+c]=8
    return rotate_grid(sprite,rng.randrange(4))


def _scene(seed, index):
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    stress=index==103
    # Bounded deterministic retries handle accidental pointer pairs, not labels.
    for attempt in range(80):
        rng=ctx.draw_rng(f'layout-{attempt}')
        h,w=(30,30) if stress else (rng.randrange(23,30),rng.randrange(23,30))
        g=[[0]*w for _ in range(h)]
        touching=(index%3==1)
        n=4 if stress else 2+(index%2)
        palette=rng.sample([1,2,3,4,5,6,7,9],8)
        sources=palette[:n]
        # Cyclic remaps prevent recursive remapping from being equivalent.
        targets=sources[1:]+sources[:1] if index%2==0 else palette[n:2*n]
        if touching:
            length=rng.randrange(12,16) if stress else rng.randrange(5,10)
            left=rng.randrange(1,4);top=1
            for r in range(length): g[top+r][left]=8
            g[top+length][left]=targets[0];g[top+length+1][left]=sources[0]
            g[top][left+1]=sources[1];g[top+1][left+1]=targets[1]
            for r in range(2,length+2):g[top+r][left+1]=8
            for i in range(2,n): _place(g,_sprite(rng,sources[i],targets[i],index+i),1,10+7*(i-2))
            seed_top=length+5
        else:
            margin=(w-7*n)//2
            for i in range(n): _place(g,_sprite(rng,sources[i],targets[i],index+i),1,margin+7*i)
            seed_top=10
        # All seed sites are separated; some are deliberately clipped by edges.
        sites=[(r,c) for r in range(seed_top,h,4) for c in range(0,w,4)]
        rng.shuffle(sites)
        count=min(len(sites),n*(4 if stress else 3))
        if count<2*n:continue
        for j,(r,c) in enumerate(sites[:count]): g[r][c]=sources[j%n]
        # Preserve unmapped distractors: they are not erased with the legend.
        unused=[v for v in palette if v not in sources and v not in targets]
        if unused:
            for r,c in sites[count:count+2]:g[r][c]=unused[0]
        g=rotate_grid(g,rng.randrange(4))
        rules=model.extract(g)
        if len(rules)!=n or sorted(t['source'] for t in rules)!=sorted(sources):continue
        if sorted((t['source'],t['target']) for t in rules)!=sorted(zip(sources,targets)):continue
        if any(len(t['offsets'])<3 for t in rules):continue
        if model.solve(g)==model.solve(g,'quarter_turn'):continue
        if stress and sum(v!=0 for row in g for v in row)<60:continue
        return g
    raise RuntimeError(f'Bounded scene construction failed: seed={seed}, index={index}')


def sample_input(seed, index):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:
        raise ValueError('seed and sample index must be nonnegative exact integers')
    return _scene(seed,index)


def generate(seed, settings, demos, queries):
    mode=setting(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid seed')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(index):
        g=sample_input(seed,index)
        return {'input':g,'output':model.solve(g,mode)}
    train=[pair(i) for i in range(demos)]
    bank=[pair(100+i) for i in range(4)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'program_solution':program(settings),
            'settings':copy.deepcopy(settings),'seed':seed,'private':{'query_bank':bank}}


def public_view(episode, turn=0, presentation_seed=0):
    if type(turn) is not int or not 0<=turn<4:raise ValueError('turn must be 0..3')
    if type(presentation_seed) is not int:raise ValueError('presentation_seed must be an integer')
    bank=episode['private']['query_bank']
    if len(bank)!=4:raise ValueError('exactly four private queries required')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']]
    return {'train':train,'test':[{'input':copy.deepcopy(bank[order[turn]]['input'])}]}
