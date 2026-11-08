"""Nested-square family for public task 45a5af55."""
from __future__ import annotations
from collections import Counter
import hashlib
import random

MODES=('full','inside_unique')
RIVALS=('use_all_rows','width_driven','reverse_layers','collapse_runs','fixed_depth_one','include_marker','center_four')


def validate_grid(grid):
    if type(grid) is not list or not 4<=len(grid)<=16 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('expected a 4..16 by 1..30 grid')
    width=len(grid[0])
    for row in grid:
        if type(row) is not list or len(row)!=width or any(type(v) is not int or not 0<=v<=9 for v in row):
            raise ValueError('expected an exact integer rectangular color grid')
        if any(v!=row[0] for v in row):
            raise ValueError('every input row must be monochrome')
    if grid[-1][0]!=grid[-2][0]:
        raise ValueError('last row must duplicate the innermost layer row')


def layer_colors(grid):
    validate_grid(grid)
    return [row[0] for row in grid[:-1]]


def render_layers(colors):
    if type(colors) is not list or not colors or len(colors)>15:
        raise ValueError('expected one to fifteen layer colors')
    side=2*len(colors)
    return [[colors[min(r,c,side-1-r,side-1-c)] for c in range(side)] for r in range(side)]


def unique_marker_depth(grid):
    colors=layer_colors(grid);counts=Counter(colors)
    depths=[i for i,color in enumerate(colors) if counts[color]==1]
    if len(depths)!=1:
        raise ValueError('inside_unique requires exactly one singleton layer color')
    depth=depths[0]
    if depth>=len(colors)-2:
        raise ValueError('singleton marker must leave a nonempty strict interior')
    return depth


def _crop_inside(full,depth):
    start=depth+1;stop=len(full)-depth-1
    if stop<=start:raise ValueError('crop is empty')
    return [row[start:stop] for row in full[start:stop]]


def solve(grid,mode='full',rival=None):
    if mode not in MODES:raise ValueError('output scope must be full or inside_unique')
    colors=layer_colors(grid);full=render_layers(colors)
    if rival is None:
        return full if mode=='full' else _crop_inside(full,unique_marker_depth(grid))
    if rival=='use_all_rows':
        return render_layers([row[0] for row in grid])
    if rival=='width_driven':
        n=max(1,len(grid[0])-1);seq=[colors[i%len(colors)] for i in range(min(n,15))]
        return render_layers(seq)
    if rival=='reverse_layers':
        return render_layers(list(reversed(colors)))
    if rival=='collapse_runs':
        seq=[]
        for color in colors:
            if not seq or seq[-1]!=color:seq.append(color)
        return render_layers(seq)
    if rival=='fixed_depth_one':
        return _crop_inside(full,1)
    if rival=='include_marker':
        depth=unique_marker_depth(grid);stop=len(full)-depth
        return [row[depth:stop] for row in full[depth:stop]]
    if rival=='center_four':
        start=(len(full)-4)//2
        return [row[start:start+4] for row in full[start:start+4]]
    raise ValueError('unknown rival')


def rng_for(seed,tag):
    if type(seed) is not int:raise ValueError('seed must be an exact integer')
    raw=hashlib.sha256(f'45a5af55/v1/{seed}/{tag}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))


_DEMO_PROFILES=((7,5,2),(9,13,4),(11,7,6),(13,19,4),(15,30,8),(9,11,2))
_QUERY_PROFILES=((9,14,2),(11,7,4),(13,21,6),(15,30,8))


def _sequence(rng,n,marker_depth):
    if n%2!=1 or marker_depth%2!=0 or not 1<=marker_depth<=n-3:
        raise ValueError('profile must pair every nonmarker layer')
    palette=rng.sample(range(10),4);marker=palette[0];bases=palette[1:]
    pairs=[]
    for start in range(0,marker_depth,2):pairs.append((start,start+1))
    for start in range(marker_depth+1,n,2):pairs.append((start,start+1))
    assignments=bases[:min(len(bases),len(pairs))]
    while len(assignments)<len(pairs):assignments.append(rng.choice(bases))
    rng.shuffle(assignments)
    seq=[None]*n;seq[marker_depth]=marker
    for pair,color in zip(pairs,assignments):
        for i in pair:seq[i]=color
    if Counter(seq)[marker]!=1 or any(count<2 for color,count in Counter(seq).items() if color!=marker):
        raise RuntimeError('invalid singleton construction')
    return seq


def sample_input(seed,index,*,query=False):
    if type(index) is not int or index<0 or type(query) is not bool:raise ValueError('invalid scene index or query flag')
    profiles=_QUERY_PROFILES if query else _DEMO_PROFILES
    n,width,depth=profiles[index%len(profiles)]
    rng=rng_for(seed,f'{"query" if query else "demo"}/{index}')
    seq=_sequence(rng,n,depth)
    return [[color]*width for color in seq+[seq[-1]]]


def query_order(seed):
    order=list(range(4));rng_for(seed,'presentation').shuffle(order);return order
