"""General crossed-wire terminal completion for official public ARC a47bf94d.

Production code has no dependency on the official examples or their labels.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_a47bf94d'
from pathlib import Path

GENERATOR_ID = TASK_ID = 'public_eval_a47bf94d'
VERSION = '1.0.0'
SUMMARY = 'Trace crossed and occluded wires; complete source diamonds and destination X symbols.'
DIRECTIONS = ((-1, 0), (0, -1), (0, 1), (1, 0))
WIRE = (5, 8, 9)
TERMINAL_COLORS = (1, 2, 3, 4, 6, 7)

def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30 or
        any(type(row) is not list or len(row) != len(grid[0]) or
            any(type(x) is not int or not 0 <= x <= 9 for x in row) for row in grid)):
        raise ValueError('Expected a rectangular integer-color grid of size 1..30')

def routes(grid):
    """Recover paths from visible endpoints, preserving heading at crossings/occlusion."""
    validate_grid(grid)
    height, width = len(grid), len(grid[0])
    def at(p):
        r, c = p
        return grid[r][c] if 0 <= r < height and 0 <= c < width else 0
    def neighbors(p):
        return [(p[0]+dr, p[1]+dc) for dr,dc in DIRECTIONS
                if at((p[0]+dr, p[1]+dc)) in WIRE]
    endpoints = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row)
                 if v in (5,8) and len(neighbors((r,c))) == 1]
    endset = set(endpoints)
    def marker(p):
        near = neighbors(p)[0]
        center = (3*p[0]-2*near[0], 3*p[1]-2*near[1])
        pixels = [at((center[0]+dr, center[1]+dc)) for dr in (-1,0,1) for dc in (-1,0,1)]
        colors = [x for x in pixels if x in TERMINAL_COLORS]
        if not colors:
            return center, 0, 'blank'
        color = colors[0]
        kind = 'solid' if len(colors) == 9 else 'x' if at(center) == color else 'diamond'
        return center, color, kind
    occluders = []
    unseen = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 9}
    while unseen:
        todo = [min(unseen)]; cells = set(todo); unseen.difference_update(cells)
        while todo:
            p = todo.pop()
            for dr,dc in DIRECTIONS:
                q = (p[0]+dr, p[1]+dc)
                if q in unseen:
                    unseen.remove(q); cells.add(q); todo.append(q)
        occluders.append(cells)
    def segment(a, b):
        dr = (b[0]>a[0])-(b[0]<a[0]); dc = (b[1]>a[1])-(b[1]<a[1])
        return [(a[0]+dr*k,a[1]+dc*k) for k in range(1, abs(b[0]-a[0])+abs(b[1]-a[1])+1)]
    result = []
    for start in endpoints:
        near = neighbors(start)[0]
        direction = (near[0]-start[0], near[1]-start[1])
        path = [start]
        states = set()
        for _ in range(2*height*width):
            current = path[-1]
            state = (current, direction)
            if state in states:
                break
            states.add(state)
            straight = (current[0]+direction[0], current[1]+direction[1])
            if at(straight) == 9:
                q = straight
                while at(q) == 9:
                    q = (q[0]+direction[0], q[1]+direction[1])
                if at(q) in (5,8):
                    path.extend(segment(current, q))
                    continue
                block = next(cells for cells in occluders if straight in cells)
                ports = []
                for br,bc in sorted(block):
                    for dr,dc in DIRECTIONS:
                        end = (br+dr,bc+dc)
                        farther = (br+2*dr,bc+2*dc)
                        if end != current and at(end) in (5,8) and at(farther) not in (0,9):
                            ports.append((end,(dr,dc)))
                if len(ports) != 1:
                    break
                end, outdir = ports[0]
                corner = (current[0],end[1]) if direction[0] == 0 else (end[0],current[1])
                path.extend(segment(current,corner)+segment(corner,end))
                direction = outdir
                continue
            if at(straight) in WIRE:
                next_cell = straight
            else:
                options = [p for p in neighbors(current) if len(path) == 1 or p != path[-2]]
                if len(options) != 1:
                    break
                next_cell = options[0]
                direction = (next_cell[0]-current[0], next_cell[1]-current[1])
            path.append(next_cell)
        end = path[-1]
        if end not in endset or start >= end:
            continue
        a, ca, ka = marker(start)
        b, cb, kb = marker(end)
        color = ca or cb
        if not color:
            continue
        if ka in ('solid', 'diamond') or kb == 'x':
            source, sink = a, b
        elif kb in ('solid', 'diamond') or ka == 'x':
            source, sink = b, a
        else:
            continue
        result.append(dict(path=path, source=source, sink=sink, color=color,
                           length=len(path)-1,
                           manhattan=abs(start[0]-end[0])+abs(start[1]-end[1])))
    return result

def paint_marker(grid, center, color, kind):
    r,c = center
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if 0 <= r+dr < len(grid) and 0 <= c+dc < len(grid[0]):
                active = abs(dr)+abs(dc) == 1 if kind == 'diamond' else abs(dr) == abs(dc)
                grid[r+dr][c+dc] = color if active else 0

def solve(grid, finish='paired', metric='length'):
    if finish not in ('paired', 'longest_sink_orange'):
        raise ValueError('Unknown finish setting')
    recovered = routes(grid)
    output = [row[:] for row in grid]
    selected = max(range(len(recovered)), key=lambda i: recovered[i][metric]) if recovered else -1
    for i, route in enumerate(recovered):
        paint_marker(output, route['source'], route['color'], 'diamond')
        color = 7 if finish == 'longest_sink_orange' and i == selected else route['color']
        paint_marker(output, route['sink'], color, 'x')
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct fresh orthogonal paths, with witnessed routing and length inversion.

    Unique elbow rows/columns prevent ambiguous merges. Crossings preserve
    heading. Occluders are retained only when the general tracer recovers the
    independently constructed route identities and lengths exactly.
    """
    from puzzle_generators.base import gen_ctx
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('seed must be an integer in 0..2**63-1')
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError('sample_index must be a nonnegative integer')
    if difficulty not in (None,'easy','medium','hard'):
        raise ValueError('Unsupported difficulty')
    if set(overrides) - {'stress'} or ('stress' in overrides and type(overrides['stress']) is not bool):
        raise ValueError('Only the exact boolean stress override is supported')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,
                difficulty=difficulty,overrides=overrides)
    rng=ctx.draw_rng('route-layout')
    stress=overrides.get('stress',False)
    n=3 if stress or difficulty=='hard' else rng.choice((2,3))
    height=30 if stress else rng.randint(28,30) if n==3 else rng.randint(21,29)
    width=30 if stress else rng.randint(29,30) if n==3 else rng.randint(23,30)
    left,right=4,width-5
    columns=list(range(6,width-7,3))
    if len(columns)<2*n:
        columns=list(range(6,width-7,2))
    source_rows=[3+4*i for i in range(n)]
    middle_rows=[r+2 for r in source_rows]
    sink_rows=[height-4-(6 if n==2 else 4)*i for i in range(n)][::-1]
    palette=rng.sample((1,2,3,4,6),n)
    def segment(a,b):
        dr=(b[0]>a[0])-(b[0]<a[0]);dc=(b[1]>a[1])-(b[1]<a[1])
        return [(a[0]+k*dr,a[1]+k*dc) for k in range(abs(b[0]-a[0])+abs(b[1]-a[1])+1)]
    for attempt in range(256):
        cols=rng.sample(columns,2*n); dest=rng.sample(sink_rows,n)
        paths=[]; corners=[]
        for i in range(n):
            pts=[(source_rows[i],left),(source_rows[i],cols[2*i]),
                 (middle_rows[i],cols[2*i]),(middle_rows[i],cols[2*i+1]),
                 (dest[i],cols[2*i+1]),(dest[i],right)]
            path=[pts[0]]
            for a,b in zip(pts,pts[1:]):path.extend(segment(a,b)[1:])
            paths.append(path);corners.extend(pts[1:-1])
        grid=[[0]*width for _ in range(height)]
        for path in paths:
            for r,c in path:grid[r][c]=8
        expected=[]
        for i,path in enumerate(paths):
            src=(source_rows[i],2);dst=(dest[i],width-3)
            if (seed+sample_index)%2:src,dst=dst,src
            expected.append((src,dst,palette[i],len(path)-1))
            style=(seed+sample_index+i)%3
            if style==0:
                for dr in (-1,0,1):
                    for dc in (-1,0,1):grid[src[0]+dr][src[1]+dc]=palette[i]
            elif style==1:paint_marker(grid,src,palette[i],'diamond')
            else:paint_marker(grid,dst,palette[i],'x')
        # Mark horizontal overpasses without altering the paths.
        for r in range(1,height-1):
            for c in range(1,width-1):
                if (grid[r][c]==8 and all(grid[r+dr][c+dc]==8 for dr,dc in DIRECTIONS)
                    and (r,c) not in corners):
                    grid[r][c-1]=grid[r][c+1]=5
        clean=routes(grid)
        if len(clean)!=n or sorted((x['source'],x['sink'],x['color'],x['length']) for x in clean)!=sorted(expected):
            continue
        best=max(range(n),key=lambda i:clean[i]['length'])
        mbest=max(range(n),key=lambda i:clean[i]['manhattan'])
        if best==mbest or sum(x['length']==clean[best]['length'] for x in clean)!=1:
            continue
        centers=list(corners)+[p for path in paths for p in path[3:-3]]
        rng.shuffle(centers)
        occluded=False
        for r,c in centers[:80]:
            box=[(rr,cc) for rr in range(r-1,r+2) for cc in range(c-1,c+2)]
            if any(not (1<=rr<height-1 and left+1<=cc<right) for rr,cc in box):continue
            trial=[row[:] for row in grid]
            for rr,cc in box:trial[rr][cc]=9
            found=routes(trial)
            if (len(found)==n and sorted((x['source'],x['sink'],x['color'],x['length']) for x in found)==sorted(expected)):
                grid=trial;occluded=True;break
        if not occluded:continue
        # Try independently randomized orientations; enforce the curriculum
        # against final reading order, never pre-rotation coordinates.
        for turns in rng.sample(range(4),4):
            rotated=grid
            for _ in range(turns):rotated=[list(row) for row in zip(*rotated[::-1])]
            found=routes(rotated)
            if len(found)!=n:continue
            index=max(range(n),key=lambda i:found[i]['length'])
            if index != (0 if sample_index%2==0 else n-1):continue
            if index == max(range(n),key=lambda i:found[i]['manhattan']):continue
            return rotated
    raise ValueError('Bounded route sampler exhausted; no silent fallback')


def self_check(grid, *, difficulty=None, meta=None):
    try:
        found=routes(grid)
        if not 2 <= len(found) <= 3:return ['Expected two or three recoverable paths']
        if len({x['source'] for x in found}|{x['sink'] for x in found})!=2*len(found):
            return ['Duplicate terminal assignment']
        return []
    except (ValueError,IndexError,StopIteration) as exc:
        return [str(exc)]
