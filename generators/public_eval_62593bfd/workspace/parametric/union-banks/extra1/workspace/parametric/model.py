"""Size-frequency edge sorting. Standalone model and input sampler.

This file and generator.py are identical portable copies: native resources cannot
escape workspace/parametric, while a relocated base generator must stand alone.
Python labels are claims; retained authoring evidence executes protected Racket.
"""
from collections import Counter
import random

GENERATOR_ID = TASK_ID = 'public_eval_62593bfd'
RULE_TASK_ID = 'ee_62593bfd'
VERSION = '1.0.0'
SUMMARY = 'Move same-sized object groups to the top and singleton sizes to the bottom.'
AXES = {}
INVARIANTS = ['strict-majority background', 'same-color eight-connected objects',
              'unchanged column coordinates', 'nonoverlapping destination footprints']


def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must be a 1..30 rectangle')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('rectangular exact integer colors 0..9 required')
    return grid


def analyze(grid, connectivity=8):
    validate_grid(grid)
    if connectivity not in (4, 8):
        raise ValueError('connectivity must be 4 or 8')
    height, width = len(grid), len(grid[0])
    bg, count = Counter(v for row in grid for v in row).most_common(1)[0]
    if count * 2 <= height * width:
        raise ValueError('admitted scenes require a strict-majority background')
    seen = set(); records = []
    steps = [(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1)
             if (dr or dc) and (connectivity == 8 or abs(dr)+abs(dc)==1)]
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == bg or (r,c) in seen:
                continue
            stack = [(r,c)]; seen.add((r,c)); cells = []
            while stack:
                a,b = stack.pop(); cells.append((a,b))
                for dr,dc in steps:
                    q = (a+dr,b+dc)
                    if (0 <= q[0] < height and 0 <= q[1] < width and q not in seen
                            and grid[q[0]][q[1]] == color):
                        seen.add(q);stack.append(q)
            cells.sort()
            r0=min(a for a,b in cells);r1=max(a for a,b in cells)
            c0=min(b for a,b in cells);c1=max(b for a,b in cells)
            records.append({'color':color,'cells':cells,'area':len(cells),
                            'bbox':(r0,c0,r1,c1),'height':r1-r0+1,'width':c1-c0+1})
    return {'background':bg,'objects':records,'height':height,'width':width}


def metric(obj, match_by):
    if match_by == 'occupied_area': return obj['area']
    if match_by == 'bbox_area': return obj['height'] * obj['width']
    if match_by == 'width': return obj['width']
    if match_by == 'height': return obj['height']
    if match_by == 'bbox_perimeter': return 2*(obj['height']+obj['width'])
    if match_by == 'color': return obj['color']
    if match_by == 'shape':
        r,c,_,_=obj['bbox']
        return tuple((a-r,b-c) for a,b in obj['cells'])
    raise ValueError('unknown match metric')


def solve(grid, match_by='occupied_area', *, connectivity=8, direction='normal', exact_pairs=False):
    data = analyze(grid, connectivity)
    objects = data['objects']; keys = [metric(o,match_by) for o in objects]
    counts = Counter(keys)
    out = [[data['background']]*data['width'] for _ in range(data['height'])]
    for obj,key in zip(objects,keys):
        paired = counts[key] == 2 if exact_pairs else counts[key] > 1
        top = paired
        if direction == 'reverse': top = not top
        elif direction == 'all_top': top = True
        elif direction == 'all_bottom': top = False
        elif direction == 'largest': top = obj['area'] == max(o['area'] for o in objects)
        elif direction == 'smallest': top = obj['area'] == min(o['area'] for o in objects)
        elif direction == 'fixed_3_4': top = obj['area'] in (3,4)
        elif direction != 'normal': raise ValueError('unknown direction')
        shift = -obj['bbox'][0] if top else data['height']-1-obj['bbox'][2]
        for r,c in obj['cells']: out[r+shift][c] = obj['color']
    return out


def mask(*rows):
    return {(r,c) for r,row in enumerate(rows) for c,v in enumerate(row) if v == '#'}


L3=mask('##','#.')
D3=mask('#..','.#.','..#')
LINE3=mask('###')
L4=mask('###','#..')
RING8=mask('###','#.#','###')
T5=mask('###','.#.','.#.')
L5=mask('##','#.','#.','#.')
T7=mask('#####','..#..','..#..')
DENSE7=mask('###','##.','##.')
SQ4=mask('##','##')
RECT8=mask('####','####')
DIAG11=mask('....#','.###.','.###.','.###.','#....')
SQ9=mask('###','###','###')
TAIL9=mask('###','#.#','###','.#.')
DIAG12=mask('#...#','.###.','.#.#.','.###.','#...#')
RECT12=mask('####','####','####')
STAIR7=mask('..###','..#..','###..')
CROSS6=mask('#...','####','.#..')
PROFILES=[(L3,D3,LINE3,L4,RING8,T5),
          (T5,L5,T7,DENSE7,SQ4,L3),
          (L3,D3,RING8,RECT8,L5,DIAG11),
          (SQ9,TAIL9,DIAG12,RECT12,STAIR7,CROSS6)]


def normalized(cells):
    lo_r=min(r for r,c in cells);lo_c=min(c for r,c in cells)
    return {(r-lo_r,c-lo_c) for r,c in cells}


def transformed(cells, rng):
    options=[]
    for transpose in (False,True):
        for sr in (-1,1):
            for sc in (-1,1):
                image=normalized({(sr*(c if transpose else r),sc*(r if transpose else c)) for r,c in cells})
                options.append(image)
    min_width=min(max(c for r,c in image)+1 for image in options)
    return rng.choice([s for s in options if max(c for r,c in s)+1<=max(3,min_width)])


def scene(seed, index, *, query=False):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng=random.Random(f'size-frequency-v1|{seed}|{index}|{query}')
    if query:
        if index not in range(4): raise ValueError('query index must be 0..3')
        height,width=[(16,24),(23,28),(30,30),(27,29)][index]
        profile=[0,2,3,1][index]
    else:
        profile=index%4
        height,width=[(18,27),(21,28),(24,29),(26,30),(19,28),(25,30)][index%6]
    shapes=[transformed(s,rng) for s in PROFILES[profile]]
    bg=rng.randrange(10)
    palette=rng.sample([v for v in range(10) if v!=bg],6)
    palette[-1]=palette[0]  # Different same-color components need not share a destination.
    items=list(zip(shapes,palette))
    extra=rng.randrange(3) if query else 0
    for i in range(extra):
        if sum(max(c for r,c in s)+1 for s,v in items)+len(items)+1 <= width:
            items.append(({(0,0)},palette[1+i]))
    rng.shuffle(items)
    widths=[max(c for r,c in s)+1 for s,v in items]
    spare=width-sum(widths)-(len(items)-1)
    if spare<0:raise ValueError('internal profile does not fit')
    # Keep both horizontal boundaries active; distribute extra space internally.
    gaps=[1]*(len(items)-1)
    for _ in range(spare):gaps[rng.randrange(len(gaps))]+=1
    grid=[[bg]*width for _ in range(height)];col=0
    for i,(cells,color) in enumerate(items):
        hh=max(r for r,c in cells)+1
        row=rng.randrange(height-hh+1)
        if query and index==2:
            if i==0:row=0
            if i==len(items)-1:row=height-hh
        for r,c in cells:grid[row+r][col+c]=color
        col+=widths[i]+(gaps[i] if i<len(gaps) else 0)
    return grid


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('unsupported difficulty or override')
    return scene(seed,sample_index%4,query=True)


def self_check(grid, *, difficulty=None, meta=None):
    try:
        data=analyze(grid)
        if len(data['objects'])<2:return ['at least two objects required']
        for choice in ('occupied_area','bbox_area'):
            keys=[metric(o,choice) for o in data['objects']];counts=Counter(keys);dest=set()
            for obj,key in zip(data['objects'],keys):
                shift=-obj['bbox'][0] if counts[key]>1 else data['height']-1-obj['bbox'][2]
                footprint={(r+shift,c) for r,c in obj['cells']}
                if dest&footprint:return ['destination objects overlap']
                dest.update(footprint)
    except (ValueError,TypeError,KeyError,IndexError) as exc:return [str(exc)]
    return []
