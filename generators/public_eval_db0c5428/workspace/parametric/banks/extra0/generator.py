"""Standalone sampler for hollow compass-tile motifs; reference labels are external.

The authored grammar keeps the parent's 3x3 tiles. A 30x30 case contains four
independent rings, not one small ring surrounded by padding. No original arrays
or answer files are imported. The native sampler is an exact resource copy.
"""
from collections import Counter
import hashlib
import random

TASK_ID = 'public_eval_db0c5428'
GENERATOR_ID = TASK_ID
RULE_TASK_ID = 'ee_db0c5428'
VERSION = '1.0.0'
SUMMARY = 'Complete a hollow compass motif and reflect its eight tiles radially.'
EXAMPLES_NEEDED = 2
AXES = {}
DIRECTIONS = [(i,j) for i in range(3) for j in range(3) if (i,j)!=(1,1)]


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError('exact integer seed and nonnegative sample_index required')
    if difficulty not in (None, 'easy', 'medium', 'hard') or overrides:
        raise ValueError('unsupported difficulty or override')
    rng = random.Random(int.from_bytes(hashlib.sha256(
        f'{TASK_ID}|{VERSION}|{seed}|{sample_index}'.encode()).digest(), 'big'))
    profile = (sample_index - 100) % 4 if sample_index >= 100 else sample_index % 4
    h,w = [(15,19),(21,23),(15,30),(30,30)][profile]
    bg = rng.randrange(10)
    grid = [[bg]*w for _ in range(h)]
    origins = ([(3,3),(3,18),(18,3),(18,18)] if profile==3 else
               [(3,3),(3,18)] if profile==2 else
               [(3+rng.randrange(h-14),3+rng.randrange(w-14))])
    for ring_index,(top,left) in enumerate(origins):
        palette = rng.sample([c for c in range(10) if c!=bg], 4)
        base = palette[0]; colors = sorted(palette[1:])
        if sample_index==0:
            colors=[colors[2],colors[0],colors[1]];counts=[1,3,4]
        elif sample_index==1:
            colors=[colors[0],colors[2],colors[1]];counts=[2,2,4]
        else:
            rng.shuffle(colors)
            counts=rng.choice(([1,3,4],[2,2,4],[1,1,6],[2,3,3],[8,0,0]))
        tips=[c for c,n in zip(colors,counts) for _ in range(n)]
        rng.shuffle(tips)
        # Sparse tile texture varies independently from tip frequency. Biasing
        # texture toward the rare tip explicitly separates pixel counts from
        # the eight semantic tip observations.
        texture=colors[0]
        for (i,j),tip in zip(DIRECTIONS,tips):
            tr=2 if i==0 else 0 if i==2 else 1
            tc=2 if j==0 else 0 if j==2 else 1
            tile=[[base]*3 for _ in range(3)]
            candidates=[(r,c) for r in range(3) for c in range(3) if (r,c)!=(tr,tc)]
            for r,c in rng.sample(candidates,2):tile[r][c]=texture
            tile[tr][tc]=tip
            for r in range(3):
                for c in range(3):grid[top+3*i+r][left+3*j+c]=tile[r][c]
    return grid


def self_check(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or not grid or
        any(type(row) is not list or len(row)!=len(grid[0]) for row in grid) or
        not 1<=len(grid[0])<=30 or
        any(type(v) is not int or not 0<=v<=9 for row in grid for v in row)):
        return ['invalid grid']
    bg=min(Counter(v for row in grid for v in row), key=lambda x:(-sum(row.count(x) for row in grid),x))
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg}
    if not remaining:return ['no ring']
    while remaining:
        start=min(remaining);remaining.remove(start);seen={start};stack=[start]
        while stack:
            r,c=stack.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p=(r+dr,c+dc)
                    if p in remaining:remaining.remove(p);seen.add(p);stack.append(p)
        top=min(r for r,c in seen);left=min(c for r,c in seen)
        expected={(top+r,left+c) for r in range(9) for c in range(9) if not (3<=r<=5 and 3<=c<=5)}
        if seen!=expected:return ['foreground must consist of complete hollow 9x9 rings']
    return []
