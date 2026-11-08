"""Recover a central directional key, then reflect addressed original tiles.

Python is an independent label claim; owner acceptance replays native Racket.
Only complete separated 3x3-tile rings are admitted by the constructive sampler.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'extension_policy':['all_tiles','largest_port_run']}
DEFAULT={'extension_policy':'all_tiles'}
RIVALS=('all_tiles','second_color','largest_color','largest_input_color','eight_connected','first_run','smallest_run','corners','edges','opposite_run','fixed_three','unreflected')
PORTS=((-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1))

def _setting(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or settings.get('extension_policy') not in PARAMETERS['extension_policy']:
        raise ValueError('settings must name exactly one declared extension_policy')
    return settings['extension_policy']

def program(settings):
    policy=_setting(settings);source=(HERE/'canonical.rkt').read_text()
    return source if policy=='all_tiles' else source.replace('(define output-policy "all_tiles")',f'(define output-policy "{policy}")',1)

def rival_programs():
    source=program(DEFAULT)
    return {name:source.replace('(define output-policy "all_tiles")',f'(define output-policy "{name}")',1) for name in RIVALS}

def _grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30
        or any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer grid, dimensions 1..30')
    return tuple(map(tuple,grid))

def _components(grid,bg,same=True,eight=False):
    H,W=len(grid),len(grid[0]);remaining={(r,c) for r in range(H) for c in range(W) if grid[r][c]!=bg};result=[]
    while remaining:
        seed=min(remaining);remaining.remove(seed);todo=[seed];cells=[seed];value=grid[seed[0]][seed[1]]
        while todo:
            r,c=todo.pop()
            for dr in range(-1,2):
                for dc in range(-1,2):
                    if (not dr and not dc) or (not eight and abs(dr)+abs(dc)!=1):continue
                    p=r+dr,c+dc
                    if p in remaining and (not same or grid[p[0]][p[1]]==value):
                        remaining.remove(p);todo.append(p);cells.append(p)
        result.append(sorted(cells))
    return result

@lru_cache(maxsize=2048)
def _analyze(grid):
    rings=[]
    for cells in _components(grid,8,same=False,eight=True):
        r0=min(r for r,c in cells);c0=min(c for r,c in cells)
        if max(r for r,c in cells)-r0!=8 or max(c for r,c in cells)-c0!=8:
            raise ValueError('each ring must contain eight complete 3x3 tiles')
        expected={(r,c) for r in range(r0,r0+9) for c in range(c0,c0+9) if not (r0+3<=r<r0+6 and c0+3<=c<c0+6)}
        if set(cells)!=expected:raise ValueError('ring must be complete except its 3x3 center hole')
        counts=Counter(grid[r][c] for r,c in cells);base=max(sorted(counts),key=counts.get)
        key=[[base]*3 for _ in range(3)]
        for dr,dc in PORTS:key[dr+1][dc+1]=grid[r0+3*(dr+1)+1-dr][c0+3*(dc+1)+1-dc]
        rings.append({'origin':[r0,c0],'base':base,'key':key,'runs':_components(key,base),
                      'input_counts':dict(counts),'cells':cells})
    if not rings:raise ValueError('no complete ring')
    return rings

def analyze(grid):return deepcopy(_analyze(_grid(grid)))

def _chosen(ring,policy):
    key,base,runs=ring['key'],ring['base'],ring['runs'];ports=[(dr+1,dc+1) for dr,dc in PORTS]
    if policy=='all_tiles':return ports
    if policy=='corners':return [(r,c) for r,c in ports if r!=1 and c!=1]
    if policy=='edges':return [(r,c) for r,c in ports if r==1 or c==1]
    if policy in ('largest_color','largest_input_color','second_color'):
        counts=(Counter(key[r][c] for r,c in ports if key[r][c]!=base) if policy!='largest_input_color' else
                {c:n for c,n in ring['input_counts'].items() if c!=base})
        if not counts:return []
        ranked=sorted(counts,key=lambda c:(-counts[c],c))
        color=ranked[min(1,len(ranked)-1)] if policy=='second_color' else ranked[0]
        return [(r,c) for r,c in ports if key[r][c]==color]
    if policy=='eight_connected':runs=_components(key,base,eight=True)
    if not runs:return []
    best=max(runs,key=len)
    if policy=='first_run':return runs[0]
    if policy=='smallest_run':return min(runs,key=len)
    if policy=='opposite_run':return [(2-r,2-c) for r,c in best]
    if policy=='fixed_three' and len(best)!=3:return []
    return best

def predict(grid,policy='all_tiles'):
    if policy not in RIVALS+('largest_port_run','second_color'):raise ValueError('unknown policy')
    rings=_analyze(_grid(grid));out=deepcopy(grid);H,W=len(grid),len(grid[0])
    for ring in rings:
        r0,c0=ring['origin']
        for r in range(3):
            for c in range(3):out[r0+3+r][c0+3+c]=ring['key'][r][c]
        for r,c in _chosen(ring,policy):
            dr,dc=r-1,c-1;sr,sc=r0+3*r,c0+3*c;tr,tc=r0+3+6*dr,c0+3+6*dc
            for i in range(3):
                for j in range(3):
                    ii=i if not dr or policy=='unreflected' else 2-i
                    jj=j if not dc or policy=='unreflected' else 2-j
                    if 0<=tr+i<H and 0<=tc+j<W:out[tr+i][tc+j]=grid[sr+ii][sc+jj]
    return out

def rotate(g,k):
    for _ in range(k%4):g=[list(row) for row in zip(*g[::-1])]
    return g

def _stamp_ring(g,r0,c0,rng,runlength):
    palette=[0,1,2,3,4,5,6,7,9];rng.shuffle(palette)
    base,A,B,C,D,E,decoration=palette[:7]
    patterns={2:[A,A,C,B,D,B,E,B],3:[A,A,A,B,B,C,B,B],
              4:[A,A,A,A,B,B,C,B],5:[A,A,A,A,A,B,C,B]}
    values=patterns[runlength];offset=rng.randrange(8);values=values[offset:]+values[:offset]
    if rng.randrange(2):values=values[::-1]
    for (dr,dc),color in zip(PORTS,values):
        sr,sc=r0+3*(dr+1),c0+3*(dc+1)
        for r in range(sr,sr+3):
            for c in range(sc,sc+3):g[r][c]=base
        facing=(1-dr,1-dc);g[sr+facing[0]][sc+facing[1]]=color
        # Ornaments have no vote in the inward-facing directional key. Their
        # frequency beats the true key color, defeating whole-ring color counts.
        free=[(r,c) for r in range(3) for c in range(3) if (r,c)!=facing]
        rng.shuffle(free)
        for r,c in free[:rng.randint(1,2)]:g[sr+r][sc+c]=decoration
    return g

def _scene(seed,index,attempt=0):
    rng=random.Random(f'db0c5428:geometry:v1:{seed}:{index}:{attempt}')
    if index==9:
        H=W=30;origins=[(3,3),(3,18),(18,3),(18,18)];lengths=[2,3,4,5]
    elif index==8:
        H,W=15,30;origins=[(3,3),(3,18)];lengths=[4,2]
    else:
        H,W=rng.randint(15,24),rng.randint(15,24)
        if index in (6,7):origins=[(0,rng.randint(0,W-9))]
        else:origins=[(rng.randint(3,H-12),rng.randint(3,W-12))]
        lengths=[[2,4,3,5,2,3,4,5][index]]
    g=[[8]*W for _ in range(H)]
    for (r,c),length in zip(origins,lengths):_stamp_ring(g,r,c,rng,length)
    g=rotate(g,rng.randrange(4));rings=_analyze(_grid(g))
    for ring in rings:
        sizes=[len(x) for x in ring['runs']]
        if not sizes or sizes.count(max(sizes))!=1:raise ValueError('largest port run must be unique')
    return g

@lru_cache(maxsize=128)
def _bank(seed):
    bank=[];seen=set();survivors=set(RIVALS)-{'all_tiles'}
    for index in range(10):
        for attempt in range(120):
            g=_scene(seed,index,attempt);key=_grid(g)
            if key in seen:continue
            rejected={n for n in survivors if predict(g,n)!=predict(g,'largest_port_run')}
            # The two-cell lesson must distinguish diagonal-only joins; the
            # four-cell lesson cannot do that on every orientation.
            if index==0 and 'eight_connected' not in rejected:continue
            if index==1 and survivors-rejected:continue
            bank.append(g);seen.add(key)
            if index<2:survivors-=rejected
            break
        else:raise ValueError(f'no distinguishing scene at slot {index}')
    if survivors:raise ValueError(f'two-demo surviving rivals: {sorted(survivors)}')
    return tuple(bank)

def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('integer seed, demos 2..6 and queries 1..4 required')
    bank=_bank(seed);perm=list(range(4));random.Random(f'db0c5428:presentation:{seed}').shuffle(perm)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in perm[:queries]],
            'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':perm}}

def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
