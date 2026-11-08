"""Native frame filling followed by input-derived area matching to a solid payload."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path
import random

TASK = '8dac9e436a4c'
PARAMETER = 'match_policy'
SETTINGS = ('fill_only', 'area_match')
RANK_RIVALS = ('median_solid','second_smallest_solid','second_largest_solid')
RIVALS = RANK_RIVALS + ('fill_only', 'smallest_filled', 'second_filled', 'largest_solid',
          'smallest_solid', 'first_solid', 'last_solid', 'dimensions_match',
          'border_count', 'outer_area', 'first_frame_only')
CANONICAL = Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError('settings must contain exactly match_policy')
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError('unknown match_policy')
    return value


def _rng(seed, role):
    return random.Random(int.from_bytes(hashlib.sha256(f'{TASK}:v1:{seed}:{role}'.encode()).digest(),'big'))


def components(grid, color):
    unseen = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack, cells = [start], []
        while stack:
            r,c = stack.pop()
            cells.append((r,c))
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen:
                    unseen.remove(p)
                    stack.append(p)
        r0,r1 = min(r for r,c in cells),max(r for r,c in cells)
        c0,c1 = min(c for r,c in cells),max(c for r,c in cells)
        result.append(dict(cells=sorted(cells),bbox=(r0,c0,r1,c1),h=r1-r0+1,w=c1-c0+1,size=len(cells)))
    return result


def analyze(grid):
    frames, solids, invalid = [], [], []
    for o in components(grid,6):
        r0,c0,r1,c1 = o['bbox']
        border = {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
                  if r in (r0,r1) or c in (c0,c1)}
        if o['h'] >= 3 and o['w'] >= 3 and set(o['cells']) == border:
            frames.append(o)
        elif o['size'] == o['h']*o['w']:
            solids.append(o)
        else:
            invalid.append(o)
    return dict(frames=frames,solids=solids,invalid=invalid)


def predict(grid, mode):
    if mode not in {*SETTINGS,*RIVALS}:
        raise ValueError(f'unknown rule: {mode}')
    info = analyze(grid)
    out = deepcopy(grid)
    frames = info['frames'][:1] if mode == 'first_frame_only' else info['frames']
    for o in frames:
        r0,c0,r1,c1 = o['bbox']
        for r in range(r0+1,r1):
            for c in range(c0+1,c1):
                out[r][c] = 8
    if mode in ('fill_only','first_frame_only'):
        return out
    filled = components(out,8)
    solids = info['solids']
    if not filled or not solids:
        return out
    largest = max(filled,key=lambda o:o['size'])
    key = largest['size']
    if mode == 'smallest_filled': key = min(o['size'] for o in filled)
    if mode == 'second_filled': key = sorted((o['size'] for o in filled),reverse=True)[min(1,len(filled)-1)]
    if mode == 'border_count': key = max((o['size'] for o in frames),default=0)
    if mode == 'outer_area': key = max((o['h']*o['w'] for o in frames),default=0)
    chosen = [o for o in solids if o['size'] == key]
    if mode == 'largest_solid': chosen = [max(solids,key=lambda o:o['size'])]
    if mode == 'smallest_solid': chosen = [min(solids,key=lambda o:o['size'])]
    if mode == 'first_solid': chosen = solids[:1]
    if mode == 'last_solid': chosen = solids[-1:]
    if mode in RANK_RIVALS:
        ordered = sorted(solids,key=lambda o:o['size'])
        index = len(ordered)//2 if mode == 'median_solid' else min(1,len(ordered)-1) if mode == 'second_smallest_solid' else max(0,len(ordered)-2)
        chosen = [ordered[index]]
    if mode == 'dimensions_match':
        chosen = [o for o in solids if sorted((o['h'],o['w'])) == sorted((largest['h'],largest['w']))]
    for o in chosen:
        for r,c in o['cells']:
            out[r][c] = 3
    return out


def rule(mode):
    if mode not in {*SETTINGS,*RIVALS}:
        raise ValueError(f'unknown rule: {mode}')
    if mode == 'fill_only':
        return CANONICAL
    # This canonical rule is a grid expression with free g, not a lambda.
    body = CANONICAL.strip()[len('(rule!'):-1].strip()
    if mode == 'first_frame_only':
        return '''(rule! (lambda (g)
          (let* ((fs (filter (lambda (o)
                     (and (= (obj-color o) 6) (>= (obj-h o) 3) (>= (obj-w o) 3)
                          (= (obj-size o) (- (* 2 (+ (obj-h o) (obj-w o))) 4))))
                     (objects g 0))))
             (if (null? fs) g
                 (let ((o (car fs)))
                   (paint-cells g (positions-in-rect (+ (obj-r1 o) 1) (+ (obj-c1 o) 1)
                                 (- (obj-r2 o) 1) (- (obj-c2 o) 1)) 8))))))'''
    key = '(obj-size largest)'
    if mode == 'smallest_filled': key = '(obj-size (pick-min filled obj-size))'
    if mode == 'second_filled': key = '(obj-size (list-ref (sort filled > #:key obj-size) (min 1 (- (length filled) 1))))'
    if mode == 'border_count': key = '(if (null? frames) 0 (obj-size (pick-max frames obj-size)))'
    if mode == 'outer_area': key = '(if (null? frames) 0 (apply max (map (lambda (o) (* (obj-h o) (obj-w o))) frames)))'
    selected = '(filter (lambda (o) (= (obj-size o) key)) solids)'
    if mode == 'largest_solid': selected = '(list (pick-max solids obj-size))'
    if mode == 'smallest_solid': selected = '(list (pick-min solids obj-size))'
    if mode == 'first_solid': selected = '(list (car solids))'
    if mode == 'last_solid': selected = '(list (last solids))'
    if mode in RANK_RIVALS:
        index = '(quotient (length solids) 2)' if mode == 'median_solid' else '(min 1 (- (length solids) 1))' if mode == 'second_smallest_solid' else '(max 0 (- (length solids) 2))'
        selected = f'(list (list-ref (sort solids < #:key obj-size) {index}))'
    if mode == 'dimensions_match': selected = '''(filter (lambda (o)
      (or (and (= (obj-h o) (obj-h largest)) (= (obj-w o) (obj-w largest)))
          (and (= (obj-h o) (obj-w largest)) (= (obj-w o) (obj-h largest))))) solids)'''
    return f'''(rule! (lambda (g)
      (let* ((base {body})
             (objs (objects base 0))
             (filled (filter (lambda (o) (= (obj-color o) 8)) objs))
             (solids (filter (lambda (o) (and (= (obj-color o) 6) (solid-rect? o))) objs))
             (frames (filter (lambda (o) (and (= (obj-color o) 6) (not (solid-rect? o)))) objs)))
        (if (or (null? filled) (null? solids)) base
            (let* ((largest (pick-max filled obj-size)) (key {key}) (selected {selected}))
              (for/fold ((out base)) ((o selected))
                (recolor-cells out (obj-cells o) 3)))))))'''


def program(settings):
    return rule(_setting(settings))


# Interior dimensions, second interior, reshaped target solid, smaller match, larger distractor.
PROFILES = (
    ((2,2),(1,3),(1,4),(1,3),(3,3)),
    ((2,3),(1,5),(1,6),(1,5),(3,3)),
    ((2,4),(1,6),(1,8),(2,3),(3,4)),
    ((3,4),(2,5),(2,6),(2,5),(4,4)),
    ((4,4),(1,10),(2,8),(2,5),(5,5)),
    ((3,3),(1,7),(1,9),(1,7),(4,4)),
)


def _spread(extra, slots, rng):
    result = [0]*slots
    for _ in range(extra):
        result[rng.randrange(slots)] += 1
    return result


def _pack(items, h, w, rng):
    """Bounded shelf packing with blank separation and dispersed boundary contacts."""
    for _ in range(128):
        order = list(items)
        rng.shuffle(order)
        shelves, row, width = [], [], 0
        for item in order:
            iw = item[2]
            if iw > w or item[1] > h:
                break
            if row and width+1+iw > w:
                shelves.append(row)
                row, width = [], 0
            width += iw+(1 if row else 0)
            row.append(item)
        else:
            if row: shelves.append(row)
            heights = [max(item[1] for item in row) for row in shelves]
            used = sum(heights)+len(shelves)-1
            if used > h:
                continue
            gaps = [1+x for x in _spread(h-used,len(shelves)-1,rng)] if len(shelves)>1 else []
            placements, top = [], (rng.randrange(h-used+1) if len(shelves)==1 else 0)
            for ri,row in enumerate(shelves):
                occupied = sum(item[2] for item in row)+len(row)-1
                cgaps = [1+x for x in _spread(w-occupied,len(row)-1,rng)] if len(row)>1 else []
                left = rng.randrange(w-occupied+1) if len(row)==1 else 0
                for ci,(kind,ih,iw) in enumerate(row):
                    rr = top+rng.randrange(heights[ri]-ih+1)
                    placements.append((kind,rr,left,ih,iw))
                    if ci < len(cgaps): left += iw+cgaps[ci]
                if ri < len(gaps): top += heights[ri]+gaps[ri]
            return placements
    raise RuntimeError(f'shelf packing exhausted: {h}x{w}')


def _candidate(rng,h,w,profile,stress):
    win, other, target, smaller, larger = PROFILES[profile]
    items = [('frame',win[0]+2,win[1]+2),('frame',other[0]+2,other[1]+2),
             ('solid',*target),('solid',*smaller),('solid',*larger)]
    if profile == 1:
        # An early teaching scene changes the target's area rank without changing
        # its equality to the reconstructed interior. No extra demo is needed.
        items += [('solid',1,1),('solid',2,5),('solid',3,4)]
    if stress:
        items += [('frame',3,3),('frame',4,4),('frame',5,5),
                  ('solid',2,6),('solid',3,6),('solid',4,5),('solid',3,7)]
    # Transpose individual items while retaining their area and the shelf bound.
    items = [(kind,iw,ih) if rng.randrange(2) and ih <= w and iw <= h else (kind,ih,iw)
             for kind,ih,iw in items]
    placements = _pack(items,h,w,rng)
    grid = [[0]*w for _ in range(h)]
    reserved = set()
    for kind,r0,c0,ih,iw in placements:
        for r in range(r0,r0+ih):
            for c in range(c0,c0+iw):
                reserved.add((r,c))
                if kind == 'solid' or r in (r0,r0+ih-1) or c in (c0,c0+iw-1):
                    grid[r][c] = 6
    # A non-role colored segment stays outside every rectangle's footprint.
    for length in (rng.randrange(1,4),1):
        runs = []
        for dr,dc in ((0,1),(1,0)):
            for r in range(h):
                for c in range(w):
                    run = [(r+i*dr,c+i*dc) for i in range(length)]
                    if all(0<=rr<h and 0<=cc<w and (rr,cc) not in reserved for rr,cc in run):
                        runs.append(run)
        if runs:
            color = rng.choice((1,2,4,5,7,9))
            for r,c in rng.choice(runs): grid[r][c] = color
            break
    if rng.randrange(2): grid = grid[::-1]
    if rng.randrange(2): grid = [row[::-1] for row in grid]
    return grid


def _scene(seed,role,dims,profile):
    rng = _rng(seed,role)
    h,w = dims
    stress = h == w == 30
    for _ in range(128):
        try:
            g = _candidate(rng,h,w,profile,stress)
        except RuntimeError:
            continue
        target = predict(g,'area_match')
        checks = RIVALS if profile == 1 else tuple(m for m in RIVALS if m not in RANK_RIVALS)
        if any(predict(g,m) == target for m in checks):
            continue
        if stress:
            cells = [(r,c) for r in range(h) for c in range(w) if g[r][c]]
            if {(r//15,c//15) for r,c in cells} != {(0,0),(0,1),(1,0),(1,1)}:
                continue
            if min(r for r,c in cells)!=0 or max(r for r,c in cells)!=29 or min(c for r,c in cells)!=0 or max(c for r,c in cells)!=29:
                continue
        return g
    raise RuntimeError(f'no teaching layout after 128 candidates: {seed}/{role}')


@lru_cache(maxsize=64)
def _inputs(seed):
    seen = set()
    def collect(role,dims,profile):
        for suffix in range(16):
            g = _scene(seed,f'{role}-{suffix}',dims,profile)
            key = tuple(map(tuple,g))
            if key not in seen:
                seen.add(key)
                return g
        raise RuntimeError('distinct input budget exhausted')
    specs = [((8,12),0),((12,16),1),((14,18),2),((18,20),3),((20,22),5),((22,24),4)]
    demos = [collect(f'demo-{i}',dims,p) for i,(dims,p) in enumerate(specs)]
    specs = [((8,12),0),((16,21),2),((24,27),3),((30,30),4)]
    _rng(seed,'query-order').shuffle(specs)
    queries = [collect(f'query-{i}',dims,p) for i,(dims,p) in enumerate(specs)]
    return demos,queries


def generate(seed,settings,demos=3,queries=4):
    _integer(seed,0,2**63-1,'seed')
    _integer(demos,2,6,'demos')
    _integer(queries,1,4,'queries')
    mode = _setting(settings)
    train,test = _inputs(seed)
    def pair(g): return {'input':deepcopy(g),'output':predict(g,mode)}
    return {'train':[pair(g) for g in train[:demos]],'test':[pair(g) for g in test[:queries]],
            'program_solution':program(settings)}


def public_turn(episode,index):
    _integer(index,0,len(episode['test'])-1,'query index')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][index]['input']}]})
