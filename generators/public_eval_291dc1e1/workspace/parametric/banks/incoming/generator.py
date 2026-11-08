"""Border-ordered multicolor strips, with an opt-in geometry-driven walk.

No original examples or answers are consulted by this implementation. Objects
are two cells thick, even-length, filled multicolor rectangles on background 8.
"""
from __future__ import annotations
from collections import Counter, deque
import random

RULE_TASK_ID = 'ee_291dc1e1'
GENERATOR_ID = TASK_ID = 'public_eval_291dc1e1'
VERSION = '1.0.0'
SUMMARY = 'Read numbered-border strip lanes, rotate vertical strips, center-stack.'
EXAMPLES_NEEDED = 2
MODES = ('canonical', 'width_walk')
INVARIANTS = ['Numbered borders meet at one top-corner zero',
              'Multicolor solid strips have thickness 2 and even length',
              'Background is 8; at most 15 objects; ARC bounds are 30']
AXES = {'axis': {'valid': 'horizontal|vertical'}, 'origin': {'valid': 'left|right'},
        'strip_length': {'valid': 'even 2..28'}, 'objects': {'valid': '1..15'},
        'color': {'valid': 'all colors except background 8'},
        'stress': {'valid': '30x30 input, 15 strips, canonical output height 30'}}
RIVALS = ('row_major', 'ignore_header_side', 'reverse_primary', 'reverse_secondary',
          'swapped_axes', 'area_sort', 'clockwise', 'transpose', 'horizontal_reflect',
          'dominant_color', 'left_align', 'right_align', 'raw_width',
          'fixed_first_stride', 'global_max_stride', 'unit_stride')


def integer(value, name, low=0, high=2**63-1):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
        or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
        or any(type(row) is not list or len(row) != len(value[0])
               or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in value)):
        raise ValueError('Expected rectangular 1..30 grid of exact integer colors 0..9')
    return [row[:] for row in value]


def ccw(tile):
    return [list(row) for row in zip(*tile)][::-1]


def cw(tile):
    return [list(row)[::-1] for row in zip(*tile)]


def components(body):
    todo = {(r,c) for r,row in enumerate(body) for c,v in enumerate(row) if v != 8}
    found = []
    while todo:
        first = min(todo);todo.remove(first);obj = [first];queue = deque([first])
        while queue:
            r,c = queue.popleft()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in todo:
                    todo.remove(q);obj.append(q);queue.append(q)
        found.append(obj)
    return found


def decode(value):
    g = grid(value)
    if len(g) < 3 or len(g[0]) < 3:
        raise ValueError('Grid is too small for numbered borders')
    left = g[0][0] == 0
    if not left and g[0][-1] != 0:
        raise ValueError('Expected one zero at a top corner')
    header = g[0][1:] if left else g[0][:-1]
    top = header[0];side = g[1][0 if left else -1]
    if (set((top,side)) != {1,2} or any(v != top for v in header)
        or any(row[0 if left else -1] != side for row in g[1:])):
        raise ValueError('Expected complete 1/2 borders meeting the origin')
    body = [row[1:] if left else row[:-1] for row in g[1:]]
    vertical = side == 1
    records = []
    for obj in components(body):
        r0=min(r for r,c in obj);r1=max(r for r,c in obj)
        c0=min(c for r,c in obj);c1=max(c for r,c in obj)
        height=r1-r0+1;width=c1-c0+1
        if len(obj) != height*width:
            raise ValueError('Objects must be filled rectangular strips')
        thick,length = (width,height) if vertical else (height,width)
        if thick != 2 or length < 2 or length%2:
            raise ValueError('Strip thickness must be 2 and length positive even')
        raw = [row[c0:c1+1] for row in body[r0:r1+1]]
        records.append({'box':(r0,c0,r1,c1), 'raw':raw})
    if not 1 <= len(records) <= 15:
        raise ValueError('Expected 1..15 separated strips')
    def key(record):
        r0,c0,r1,c1=record['box']
        return (c0 if left else -c1,r0) if vertical else (r0,c0 if left else -c1)
    records.sort(key=key)
    return {'vertical':vertical, 'left':left, 'records':records,
            'boxes':[x['box'] for x in records],
            'tiles':[ccw(x['raw']) if vertical else x['raw'] for x in records]}


def walk_indices(tiles, steps=None):
    """Follow the per-current-object jump, never a single frozen stride."""
    steps = [len(tile[0])//2 for tile in tiles] if steps is None else steps
    if len(steps) != len(tiles) or any(type(n) is not int or n < 1 for n in steps):
        raise ValueError('Walk steps must be positive exact integers, one per strip')
    indices=[];i=0
    while i < len(tiles):
        indices.append(i);i += steps[i]
    return indices


def solve(value, mode='canonical', *, rival=None):
    if mode not in MODES:raise ValueError('Undeclared mode')
    if rival is not None and rival not in RIVALS:raise ValueError('Undeclared rival')
    d=decode(value);records=list(d['records'])
    def key(rec):
        r,c,r1,c1=rec['box']
        secondary,primary = ((c if d['left'] else -c1),r) if d['vertical'] else (r,(c if d['left'] else -c1))
        if rival=='row_major':return (r,c)
        if rival=='ignore_header_side':return (c,r) if d['vertical'] else (r,c)
        if rival=='reverse_primary':return (secondary,-primary)
        if rival=='reverse_secondary':return (-secondary,primary)
        if rival=='swapped_axes':return (primary,secondary)
        if rival=='area_sort':return ((r1-r+1)*(c1-c+1),secondary,primary)
        return (secondary,primary)
    records.sort(key=key)
    tiles=[]
    for record in records:
        raw=record['raw']
        if d['vertical']:
            tile=cw(raw) if rival=='clockwise' else [list(x) for x in zip(*raw)] if rival=='transpose' else ccw(raw)
        else:tile=[row[:] for row in raw]
        if rival=='horizontal_reflect':tile=[row[::-1] for row in tile]
        if rival=='dominant_color':
            color=Counter(v for row in tile for v in row).most_common(1)[0][0]
            tile=[[color]*len(tile[0]) for row in tile]
        tiles.append(tile)
    if mode=='width_walk':
        steps=[len(tile[0])//2 for tile in tiles]
        if rival=='raw_width':steps=[len(rec['raw'][0])//2 for rec in records]
        if rival=='fixed_first_stride':steps=[steps[0]]*len(steps)
        if rival=='global_max_stride':steps=[max(steps)]*len(steps)
        if rival=='unit_stride':steps=[1]*len(steps)
        indices=walk_indices(tiles,steps)
        tiles=[tiles[i] for i in indices]
    width=max(len(tile[0]) for tile in tiles)
    output=[]
    for tile in tiles:
        padding=width-len(tile[0])
        left=0 if rival=='left_align' else padding if rival=='right_align' else padding//2
        output.extend([[8]*left+row+[8]*(padding-left) for row in tile])
    return output


def self_check(value, *, difficulty=None, meta=None):
    try:decode(value)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []


def _positions(lengths, span, rng, *, spread=False):
    # One background cell on both outer edges and at least one between objects.
    free=span-2-sum(lengths)-(len(lengths)-1)
    if free < 0:raise ValueError('Layout does not fit')
    gaps=[1]*(len(lengths)-1)
    before=0
    if spread and len(lengths)>1:
        for _ in range(free):gaps[rng.randrange(len(gaps))]+=1
    else:
        buckets=[0]*(len(lengths)+1)
        for _ in range(free):buckets[rng.randrange(len(buckets))]+=1
        before=buckets[0]
        for i in range(len(gaps)):gaps[i]+=buckets[i+1]
    result=[];at=1+before
    for i,length in enumerate(lengths):
        result.append(at);at+=length+(gaps[i] if i<len(gaps) else 0)
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    integer(seed,'seed');integer(sample_index,'sample_index')
    if difficulty not in (None,'easy','medium','hard','mixed'):raise ValueError('Unknown difficulty')
    if overrides:raise ValueError('Unknown generation overrides: '+','.join(sorted(overrides)))
    rng=random.Random(f'{TASK_ID}:{VERSION}:{seed}:{sample_index}')
    profile=sample_index%10;stress=profile==9
    if profile==0:
        lanes=[3,3,3];lengths=[4,6,2,4,2,4,6,2,4];vertical=True;left=bool(rng.getrandbits(1))
    elif profile==1:
        lanes=[3,3];lengths=[6,2,4,4,6,2];vertical=False;left=False
    elif stress:
        lanes=[3]*5;lengths=[rng.choice((2,4,6,8)) for _ in range(15)]
        lengths[:3]=[4,6,2];vertical=True;left=bool(rng.getrandbits(1))
    elif profile==8:
        lanes=[1,2];lengths=[26,4,6];vertical=bool(rng.getrandbits(1));left=bool(rng.getrandbits(1))
    elif profile==6:
        lanes=[2];lengths=[2,4];vertical=bool(rng.getrandbits(1));left=bool(rng.getrandbits(1))
    else:
        lanes=[rng.randint(1,3) for _ in range(rng.randint(2,4))]
        lengths=[rng.choice((2,4,6)) for _ in range(sum(lanes))]
        vertical=bool(rng.getrandbits(1));left=bool(rng.getrandbits(1))
    rows=[];start=0
    for count in lanes:
        rows.append(lengths[start:start+count]);start+=count
    required=max(sum(row)+len(row)-1 for row in rows)
    primary=29 if stress else min(29,required+2+rng.randint(0,3))
    secondary=29 if stress else 2*len(lanes)+(len(lanes)-1)*2+2+rng.randint(0,3)
    height,width=(primary,secondary) if vertical else (secondary,primary)
    body=[[8]*width for _ in range(height)]
    lane_positions=[1,7,13,19,26] if stress else _positions([2]*len(lanes),secondary,rng)
    palette=rng.sample([0,1,2,3,4,5,6,7,9],9);index=0
    for lane,(length_row,spos) in enumerate(zip(rows,lane_positions)):
        for length,ppos in zip(length_row,_positions(length_row,primary,rng,spread=stress)):
            base=palette[index%9];accent=palette[(index+1)%9];third=palette[(index+4)%9]
            tile=[[base]*length for _ in range(2)]
            for r in range(2):
                for c in range(length):
                    if rng.random()<.10:tile[r][c]=rng.choice(palette)
            tile[0][0]=accent;tile[0][-1]=base;tile[1][0]=base;tile[1][-1]=third
            if length>=4:tile[0][length//2]=third
            if vertical:
                raw=cw(tile);r0=ppos;c0=spos if left else secondary-spos-2
            else:
                raw=tile;r0=spos;c0=ppos if left else primary-ppos-length
            for dr,row in enumerate(raw):body[r0+dr][c0:c0+len(row)]=row[:]
            index+=1
    top,side=(2,1) if vertical else (1,2)
    output=([[0]+[top]*width]+[[side]+row for row in body]) if left else ([[top]*width+[0]]+[row+[side] for row in body])
    decoded=decode(output)
    if len(decoded['tiles']) != len(lengths):raise RuntimeError('Generated component collision')
    return output


def teaching_failures(episode, mode):
    failures=[]
    for rival in RIVALS:
        if all(solve(p['input'],mode,rival=rival)==p['output'] for p in episode['train']):
            for index,pair in enumerate(episode['test']):
                if solve(pair['input'],mode,rival=rival)!=pair['output']:
                    failures.append({'rival':rival,'query_index':index});break
    return failures
