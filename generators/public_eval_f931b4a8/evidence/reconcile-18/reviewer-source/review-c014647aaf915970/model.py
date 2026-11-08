"""Count-controlled two-scale compositing, independent Python oracle and sampler."""
from __future__ import annotations
from functools import lru_cache
import hashlib
import random


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('Expected a 1..30 rectangular grid')
    if any(type(row) is not list or len(row) != len(grid[0]) or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('Expected exact color integers and equal row lengths')


def analyze(grid):
    grid_check(grid)
    if len(grid) != len(grid[0]) or len(grid) % 2:
        raise ValueError('Input must be an even square with four equal quadrants')
    side = len(grid)//2
    top_left = [row[:side] for row in grid[:side]]
    top_right = [row[side:] for row in grid[:side]]
    height = sum(v != 0 for row in top_left for v in row)
    width = sum(v != 0 for row in top_right for v in row)
    integer(height,1,30,'output height');integer(width,1,30,'output width')
    palette = [row[:side] for row in grid[side:]]
    stencil = [row[side:] for row in grid[side:]]
    return side,height,width,palette,stencil


def backing(grid, mode):
    side,height,width,palette,stencil=analyze(grid)
    if mode=='block' and any(v for row in stencil for v in row):return [[palette[r//side][c//side] for c in range(width)] for r in range(height)]
    return [[palette[r%side][c%side] for c in range(width)] for r in range(height)]


def solve(grid, mode):
    side,height,width,palette,stencil=analyze(grid)
    base=backing(grid,mode)
    return [[stencil[r%side][c%side] or base[r][c] for c in range(width)] for r in range(height)]


def rng_for(seed,stream):
    return random.Random(int.from_bytes(hashlib.sha256(f'quadrants-v1:{seed}:{stream}'.encode()).digest(),'big'))


def sample_grid(seed,stream,profile):
    side,height,width=profile
    if not 1<=height<=min(30,side*side) or not 1<=width<=min(30,side*side):
        raise ValueError('Counts outside quadrant/output capacity')
    rng=rng_for(seed,stream)
    # Counter values are not a lookup of quadrant size or source ordinal.
    if side == 2:
        height,width=rng.sample([3,4],2)
    elif side == 3:
        height,width=rng.sample(list(range(4,10)),2)
    elif side == 7:
        height,width=rng.sample([x for x in range(20,31) if x%side],2)
    elif side != 15:
        height=max(1,min(30,side*side,height+rng.randint(-2,2)))
        width=max(1,min(30,side*side,width+rng.randint(-2,2)))
    grid=[[0]*(2*side) for _ in range(2*side)]
    for offset,count in [(0,height),(side,width)]:
        positions=rng.sample(range(side*side),count)
        colors=rng.sample(range(1,10),min(4,count))
        for i,pos in enumerate(positions):grid[pos//side][offset+pos%side]=colors[i%len(colors)]
    palette=[[rng.randrange(10) for _ in range(side)] for _ in range(side)]
    # Expose all coarse/fine directions with distinct nearby colors, including zero.
    local_colors=rng.sample(range(10),4)
    palette[0][0],palette[0][1],palette[1][0],palette[1][1]=local_colors
    stencil=[[0 if rng.random()<0.5 else rng.randint(1,9) for _ in range(side)] for _ in range(side)]
    stencil[0][0]=rng.randint(1,9)
    for r,c in [(0,1),(1,0),(side-1,side-1)]:stencil[r][c]=0
    if stream=='train:0' or (stream=='query:1' and seed%5==0):
        stencil=[[0]*side for _ in range(side)]  # Teach the absent-stencil identity, not only nonempty overlays.
    if stream=='query:2' and seed%7==0:stencil=[[rng.randint(1,9) for _ in range(side)] for _ in range(side)]
    for r in range(side):grid[side+r]=palette[r]+stencil[r]
    return grid


@lru_cache(maxsize=128)
def bank(seed):
    train_profiles=[(3,8,7),(7,26,29),(4,11,14),(5,19,23),(8,27,22),(10,28,25)]
    query_profiles=[(2,3,4),(4,10,13),(6,17,29),(15,30,30)]
    train=[sample_grid(seed,f'train:{i}',p) for i,p in enumerate(train_profiles)]
    test=[sample_grid(seed,f'query:{i}',p) for i,p in enumerate(query_profiles)]
    rng_for(seed,'presentation').shuffle(test)
    return train,test
