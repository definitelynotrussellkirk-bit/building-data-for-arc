"""Eight-connected object counts and ranked cumulative counting boards.

Generation is self-contained and reads no parent puzzles. Python claims are
independently executed by protected Racket during tests, audit and preflight.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'board_policy':['count_all','ranked_cumulative']}
DEFAULT={'board_policy':'count_all'}
RIVALS=('count_all','four_connected','pixels','shape_classes','include_legend','rank_only','cumulative_input_order','descending_cumulative')

def _setting(settings):
    if (type(settings) is not dict or set(settings)!=set(PARAMETERS)
        or type(settings['board_policy']) is not str or settings['board_policy'] not in PARAMETERS['board_policy']):
        raise ValueError('settings must name exactly one declared board_policy')
    return settings['board_policy']

def program(settings):
    policy=_setting(settings);s=(HERE/'canonical.rkt').read_text()
    return s if policy=='count_all' else s.replace('(define output-policy "count_all")',f'(define output-policy "{policy}")',1)

def rival_programs():
    s=program(DEFAULT)
    return {name:s.replace('(define output-policy "count_all")',f'(define output-policy "{name}")',1) for name in RIVALS}

def _grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
        or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer 1..30 color grid')
    return tuple(tuple(row) for row in grid)

def components(grid,bg,diagonal=True):
    left={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg};result=[]
    moves=[(r,c) for r in (-1,0,1) for c in (-1,0,1) if (r or c) and (diagonal or abs(r)+abs(c)==1)]
    while left:
        first=min(left);left.remove(first);todo=[first];part=[first]
        while todo:
            r,c=todo.pop()
            for dr,dc in moves:
                p=r+dr,c+dc
                if p in left and grid[p[0]][p[1]]==grid[first[0]][first[1]]:
                    left.remove(p);todo.append(p);part.append(p)
        result.append(sorted(part))
    return result

@lru_cache(maxsize=512)
def _analyze(grid):
    zeros=[p for p in components(grid,-1,False) if grid[p[0][0]][p[0][1]]==0]
    if not zeros:raise ValueError('a black counting board is required')
    cells=max(zeros,key=len);r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    r1=max(r for r,c in cells);c1=max(c for r,c in cells)
    values=[v for r,row in enumerate(grid) for c,v in enumerate(row) if not (r0<=r<=r1 and c0<=c<=c1)]
    if not values:raise ValueError('objects must appear outside the board')
    bg=max(sorted(set(values)),key=values.count)
    outside=[list(row) for row in grid]
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):outside[r][c]=bg
    parts=components(outside,bg,True);parts4=components(outside,bg,False)
    entries=[]
    for r in range(r0,r1+1):
        marked=[c for c in range(c0,c1+1) if grid[r][c]!=0]
        if marked:
            c=marked[0];color=grid[r][c]
            matching=[p for p in parts if outside[p[0][0]][p[0][1]]==color]
            shapes={tuple((rr-min(x[0] for x in p),cc-min(x[1] for x in p)) for rr,cc in p) for p in matching}
            entries.append({'row':r-r0,'column':c-c0,'color':color,'count':len(matching),
                'pixels':sum(map(len,matching)),'shape_classes':len(shapes),
                'four_connected':sum(outside[p[0][0]][p[0][1]]==color for p in parts4)})
    return {'bbox':[r0,c0,r1,c1],'background':bg,'height':r1-r0+1,'width':c1-c0+1,
            'entries':entries,'outside_colors':sorted({outside[p[0][0]][p[0][1]] for p in parts}),
            'components':parts,'four_components':parts4}

def analyze(grid):return deepcopy(_analyze(_grid(grid)))

def predict(grid,policy='count_all'):
    if policy not in RIVALS+('ranked_cumulative',):raise ValueError('unknown board policy')
    info=_analyze(_grid(grid));entries=deepcopy(info['entries'])
    if policy in ('four_connected','pixels','shape_classes'):
        for e in entries:e['count']=e[policy]
    if policy=='include_legend':
        for e in entries:e['count']+=1
    if policy in ('count_all','cumulative_input_order'):ordered=entries
    else:ordered=sorted(entries,key=lambda e:e['count'],reverse=policy=='descending_cumulative')
    out=[[0]*info['width'] for _ in range(info['height'])];total=0
    for slot,item in zip(entries,ordered):
        total+=item['count'];n=item['count'] if policy in ('count_all','rank_only') else total
        for c in range(slot['column'],min(info['width'],slot['column']+2*n),2):out[slot['row']][c]=item['color']
    return out

# Includes diagonally connected X/diamond shapes and repeated translated shapes.
SHAPES=( ((0,0),(0,2),(1,1),(2,0),(2,2)),
         ((0,0),(0,1),(1,0),(1,1)),
         ((0,1),(1,0),(1,1),(1,2),(2,1)),
         ((0,1),(1,0),(1,2),(2,1)) )

def _scene(seed,index):
    rng=random.Random(f'58490d8a:inputs:v1:{seed}:{index}')
    h=25+index%5;w=26+index%5
    low,middle,high=rng.randint(1,2),rng.randint(3,4),rng.randint(5,6)
    counts=(middle,high,low) if index%2==0 else (high,low,middle)
    if index==9:
        h=w=30
        counts=list(rng.choice(((1,2,4,5),(1,3,4,5),(2,3,4,5),(1,2,3,6))))
        rng.shuffle(counts)
    palette=list(range(1,10));rng.shuffle(palette)
    bg=palette[0];colors=palette[1:1+len(counts)];ignored=palette[-1]
    bh=2*len(counts)+1;bw=w-rng.randrange(2)
    if bw>w:raise ValueError('counting board does not fit')
    r0=h-bh;c0=rng.randrange(w-bw+1)
    g=[[bg]*w for _ in range(h)]
    for r in range(r0,h):
        for c in range(c0,c0+bw):g[r][c]=0
    for i,col in enumerate(colors):g[r0+2*i+1][c0+1]=col
    slots=[(r,c) for r in range(1,r0-2,4) for c in range(1,w-2,5)]
    rng.shuffle(slots)
    specifications=[(color,j) for color,n in zip(colors,counts) for j in range(n)]
    specifications += [(ignored,j) for j in range(3)]
    if len(slots)<len(specifications):raise ValueError('insufficient non-touching object slots')
    for (color,j),(r,c) in zip(specifications,slots):
        shape=SHAPES[0] if j%2==0 else SHAPES[1+rng.randrange(3)]
        # Independent reflection keeps some shapes structurally different while
        # every shape has one eight-connected component.
        if rng.randrange(2):shape=tuple((a,2-b) for a,b in shape)
        for dr,dc in shape:g[r+dr][c+dc]=color
    info=analyze(g)
    if [e['count'] for e in info['entries']]!=list(counts):raise ValueError('placement changed object counts')
    return g

@lru_cache(maxsize=128)
def _bank(seed):return tuple(_scene(seed,i) for i in range(10))

def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('integer seed, demonstrations 2..6 and queries 1..4 required')
    bank=_bank(seed);permutation=list(range(4));random.Random(f'58490d8a:presentation:{seed}').shuffle(permutation)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in permutation[:queries]],
        'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':permutation}}

def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
        'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
