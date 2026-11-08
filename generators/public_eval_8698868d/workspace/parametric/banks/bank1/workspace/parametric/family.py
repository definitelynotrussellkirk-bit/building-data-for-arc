"""Topological-key template matching, with a matched-input area alternative.

This module contains no original example or answer data. All colors, including
zero, can be foreground; the unique modal color is the scene background.
"""
from __future__ import annotations
from collections import Counter, namedtuple
from functools import lru_cache
import hashlib
import random

SETTINGS=('component_count','background_area')
CARDINAL=((-1,0),(1,0),(0,-1),(0,1))
ALL_EIGHT=tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc)
Shape=namedtuple('Shape','color top left side pixels holes')


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def setting(settings):
    if type(settings) is not dict or set(settings)!={'matching'} or settings['matching'] not in SETTINGS:
        raise ValueError('settings must contain exactly matching=component_count or background_area')
    return settings['matching']


def _rng(seed,*keys):
    return random.Random(int.from_bytes(hashlib.sha256('|'.join(map(str,('8698868d-v1',seed,*keys))).encode()).digest(),'big'))


def component_count(positions,eight=False):
    remaining=set(positions); count=0
    deltas=ALL_EIGHT if eight else CARDINAL
    while remaining:
        stack=[min(remaining)]; remaining.remove(stack[0]); count+=1
        while stack:
            r,c=stack.pop()
            for dr,dc in deltas:
                p=(r+dr,c+dc)
                if p in remaining:
                    remaining.remove(p); stack.append(p)
    return count


def _grid_key(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('expected a nonempty 1..30 rectangular grid')
    width=len(grid[0])
    if any(type(row) is not list or len(row)!=width or
           any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('grid colors must be exact integers in 0..9')
    return tuple(tuple(row) for row in grid)


def background(grid):
    key=_grid_key(grid)
    counts=Counter(v for row in key for v in row)
    top=counts.most_common()
    if len(top)>1 and top[0][1]==top[1][1]: raise ValueError('background must be uniquely modal')
    return top[0][0]


@lru_cache(maxsize=512)
def _decode(key):
    counts=Counter(v for row in key for v in row); ranked=counts.most_common()
    if len(ranked)>1 and ranked[0][1]==ranked[1][1]: raise ValueError('background must be uniquely modal')
    bg=ranked[0][0]
    remaining={(r,c) for r,row in enumerate(key) for c,v in enumerate(row) if v!=bg}
    shapes=[]
    while remaining:
        start=min(remaining); color=key[start[0]][start[1]]
        remaining.remove(start); stack=[start]; cells={start}
        while stack:
            r,c=stack.pop()
            for dr,dc in CARDINAL:
                p=(r+dr,c+dc)
                if p in remaining and key[p[0]][p[1]]==color:
                    remaining.remove(p);stack.append(p);cells.add(p)
        r0=min(r for r,c in cells); r1=max(r for r,c in cells)
        c0=min(c for r,c in cells); c1=max(c for r,c in cells)
        side=r1-r0+1
        if side!=c1-c0+1 or side<2: raise ValueError('foreground objects must be square frames')
        pixels=tuple(tuple(key[r][c0:c1+1]) for r in range(r0,r1+1))
        if (any(pixels[r][c]!=color for r in range(side) for c in range(side)
                if r in (0,side-1) or c in (0,side-1)) or
            any(v not in (color,bg) for row in pixels for v in row)):
            raise ValueError('complete monochrome square frames required')
        holes=frozenset((r,c) for r,row in enumerate(pixels) for c,v in enumerate(row) if v==bg)
        shapes.append(Shape(color,r0,c0,side,pixels,holes))
    if not shapes: raise ValueError('no tiles or templates')
    size=max(o.side for o in shapes)
    tiles=tuple(o for o in shapes if o.side==size)
    templates=tuple(o for o in shapes if o.side==size-2)
    if not tiles or len(tiles)!=len(templates) or len(shapes)!=len(tiles)+len(templates):
        raise ValueError('require equal numbers of S tiles and S-2 templates')
    r0=min(o.top for o in tiles); c0=min(o.left for o in tiles)
    r1=max(o.top+size for o in tiles); c1=max(o.left+size for o in tiles)
    covered={(r,c) for o in tiles for r in range(o.top,o.top+size) for c in range(o.left,o.left+size)}
    if len(covered)!=(r1-r0)*(c1-c0): raise ValueError('tiles must form a complete rectangular panel')
    return {'background':bg,'tiles':tiles,'templates':templates,'bounds':(r0,c0,r1,c1),'size':size}


def decode(grid):
    # Return a new mapping over immutable Shape records; callers cannot poison the cache.
    return dict(_decode(_grid_key(grid)))


def metric(obj, matching):
    if matching=='component_count': return component_count(obj.holes)
    if matching=='background_area': return len(obj.holes)
    if matching=='eight_connected': return component_count(obj.holes,eight=True)
    raise ValueError('unknown matching metric')


def _rotate(grid):
    return tuple(tuple(row) for row in zip(*grid[::-1]))


def _select(scene, matching, rival=None):
    templates=scene['templates']; tiles=scene['tiles']
    selected=[]
    for i,tile in enumerate(tiles):
        if rival=='first_template': target=templates[0]
        elif rival=='last_template': target=templates[-1]
        elif rival=='same_color': target=next((o for o in templates if o.color==tile.color),templates[0])
        elif rival=='nearest_template':
            target=min(templates,key=lambda o:abs(2*o.top+o.side-(2*tile.top+tile.side))+abs(2*o.left+o.side-(2*tile.left+tile.side)))
        elif rival=='sorted_colors': target=sorted(templates,key=lambda o:o.color)[i]
        elif rival=='cycle_components':
            value=metric(tile,'component_count')
            if value==0:
                target=next(o for o in templates if metric(o,'component_count')==0)
            else:
                ordered=sorted((o for o in templates if metric(o,'component_count')>0),
                               key=lambda o:metric(o,'component_count'))
                rank=sum(metric(o,'component_count')<value for o in ordered)
                target=ordered[(rank+1)%len(ordered)]
        else:
            rule=(SETTINGS[1-SETTINGS.index(matching)] if rival=='other_metric' else
                  'eight_connected' if rival=='eight_connected' else matching)
            value=metric(tile,rule)
            candidates=[o for o in templates if metric(o,rule)==value]
            if rival=='reverse_metric_rank':
                ordered=sorted(templates,key=lambda o:metric(o,rule))
                rank=sum(metric(o,rule)<value for o in templates)
                target=ordered[len(ordered)-1-min(rank,len(ordered)-1)]
            elif rival=='eight_connected': target=candidates[0] if candidates else templates[0]
            else:
                if len(candidates)!=1: raise ValueError('matching key must select exactly one loose template')
                target=candidates[0]
        selected.append(target)
    return selected


def _render(scene, selected, rival=None):
    r0,c0,r1,c1=scene['bounds']; bg=scene['background']; size=scene['size']
    out=[[bg]*(c1-c0) for _ in range(r1-r0)]
    for tile,template in zip(scene['tiles'],selected):
        pixels=_rotate(template.pixels) if rival=='rotate_stamp' else template.pixels
        for r in range(size):
            for c in range(size):
                value=tile.color
                if 1<=r<size-1 and 1<=c<size-1:
                    value=pixels[r-1][c-1]
                    if value==bg and rival!='unrebased_background': value=tile.color
                out[tile.top-r0+r][tile.left-c0+c]=value
    return out


def solve(grid, matching='component_count'):
    if matching not in SETTINGS: raise ValueError('unknown matching setting')
    scene=decode(grid)
    return _render(scene,_select(scene,matching))


def rival_names(matching):
    if matching not in SETTINGS: raise ValueError('unknown matching setting')
    return ('other_metric','eight_connected','first_template','last_template','same_color',
            'nearest_template','sorted_colors','reverse_metric_rank','unrebased_background','rotate_stamp','cycle_components')


def rival_solve(grid, matching, name):
    if name not in rival_names(matching): raise ValueError('unknown rival')
    scene=decode(grid)
    return _render(scene,_select(scene,matching,name),name)


def racket_program(matching='component_count', rival=None):
    if matching not in SETTINGS: raise ValueError('unknown matching setting')
    if rival is not None and rival not in rival_names(matching): raise ValueError('unknown rival')
    chosen=SETTINGS[1-SETTINGS.index(matching)] if rival=='other_metric' else matching
    measure=('(length (objects-8 (crop o) (obj-color o)))' if rival=='eight_connected' else
             '(count-color (crop o) bg)' if chosen=='background_area' else
             '(length (objects (crop o) (obj-color o)))')
    selector='''(let ((found (filter (lambda (o) (= (measure o) (measure tile))) templates)))
          (first found))'''
    if rival=='eight_connected':
        selector='''(let ((found (filter (lambda (o) (= (measure o) (measure tile))) templates)))
          (if (empty? found) (first templates) (first found)))'''
    elif rival=='first_template': selector='(first templates)'
    elif rival=='last_template': selector='(last templates)'
    elif rival=='same_color':
        selector='''(let ((found (filter (lambda (o) (= (obj-color o) (obj-color tile))) templates)))
          (if (empty? found) (first templates) (first found)))'''
    elif rival=='nearest_template':
        selector='''(pick-min templates (lambda (o)
          (+ (abs (- (+ (* 2 (obj-r1 o)) (obj-h o)) (+ (* 2 (obj-r1 tile)) (obj-h tile))))
             (abs (- (+ (* 2 (obj-c1 o)) (obj-w o)) (+ (* 2 (obj-c1 tile)) (obj-w tile)))))))'''
    elif rival=='sorted_colors':
        selector='''(list-ref (sort templates (lambda (a b) (< (obj-color a) (obj-color b))))
          (count-if (lambda (o) (before? o tile)) tiles))'''
    elif rival=='reverse_metric_rank':
        selector='''(list-ref (sort templates (lambda (a b) (< (measure a) (measure b))))
          (- (length templates) 1 (count-if (lambda (o) (< (measure o) (measure tile))) templates)))'''
    elif rival=='cycle_components':
        selector='''(let ()
          (define (holes o) (length (objects (crop o) (obj-color o))))
          (define positive (sort (filter (lambda (o) (> (holes o) 0)) templates)
                                 (lambda (a b) (< (holes a) (holes b)))))
          (if (= (holes tile) 0)
              (first (filter (lambda (o) (= (holes o) 0)) templates))
              (list-ref positive (modulo (+ 1 (count-if (lambda (o) (< (holes o) (holes tile))) positive)) (length positive)))))'''
    rebased='v' if rival=='unrebased_background' else '(if (= v bg) (obj-color tile) v)'
    pattern='(rotate-cw (crop chosen))' if rival=='rotate_stamp' else '(crop chosen)'
    return f'''(rule!
 ;; Background is the unique modal color, including zero as a possible foreground.
 ;; The largest square objects tile a panel; detached S-2 squares are templates.
 ;; Match using {chosen.replace('_',' ')}; component connectivity is four, not eight.
 ;; Inset the selected pattern by one cell and replace its background with tile color.
 ;; Erase the original clues and return only the completed panel's bounding rectangle.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define all (objects g bg))
   (define size (apply max (map obj-h all)))
   (define tiles (filter (lambda (o) (and (= (obj-h o) size) (= (obj-w o) size))) all))
   (define templates (filter (lambda (o) (and (= (obj-h o) (- size 2)) (= (obj-w o) (- size 2)))) all))
   (define (crop o) (subgrid g (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)))
   (define (measure o) {measure})
   (define (before? a b) (or (< (obj-r1 a) (obj-r1 b)) (and (= (obj-r1 a) (obj-r1 b)) (< (obj-c1 a) (obj-c1 b)))))
   (define box (bbox-of-cells (apply append (map obj-cells tiles))))
   (define blank (empty-grid (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box))) bg))
   (for/fold ((out blank)) ((tile tiles))
    (let* ((chosen {selector})
           (pattern {pattern}))
     (for*/fold ((a out)) ((r (range size)) (c (range size)))
      (let ((value (if (and (> r 0) (< r (- size 1)) (> c 0) (< c (- size 1)))
                      (let ((v (at pattern (- r 1) (- c 1)))) {rebased})
                      (obj-color tile))))
       (set-cell a (+ (- (obj-r1 tile) (first box)) r) (+ (- (obj-c1 tile) (second box)) c) value))))))))
'''


def _regions(side, count, area, rng):
    """Grow separated hole components, preserving a connected surrounding frame."""
    if count==0: return frozenset() if area==0 else None
    if not count<=area<=side*side: return None
    if count==1 and area==side*side:
        return frozenset((r,c) for r in range(side) for c in range(side))
    all_cells=[(r,c) for r in range(side) for c in range(side)]
    for _ in range(256):
        labels={}
        if side==3 and count==5:
            labels={p:i for i,p in enumerate(all_cells) if sum(p)%2==0}
        else:
            for group in range(count):
                allowed=[p for p in all_cells if p not in labels and
                         all((p[0]+dr,p[1]+dc) not in labels for dr,dc in CARDINAL)]
                if not allowed: break
                labels[rng.choice(allowed)]=group
        if len(labels)!=count: continue
        while len(labels)<area:
            frontier=[]
            for r,c in all_cells:
                if (r,c) in labels: continue
                touching={labels[(r+dr,c+dc)] for dr,dc in CARDINAL if (r+dr,c+dc) in labels}
                if len(touching)==1: frontier.append(((r,c),next(iter(touching))))
            if not frontier: break
            p,group=rng.choice(frontier); labels[p]=group
        if len(labels)!=area: continue
        occupied=set(labels)
        surrounding={(r,c) for r in range(side+2) for c in range(side+2)}-{(r+1,c+1) for r,c in occupied}
        if component_count(surrounding)==1:
            return frozenset(occupied)
    return None


def _separated(a,b):
    """Half-open rectangles, with at least one complete background cell gap."""
    return a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1]


def _candidate(seed,role,index,attempt=0,stress=False):
    rng=_rng(seed,role,index,attempt)
    if stress:
        size,n,h,w=7,6,30,30
    elif role=='train' and index==1:
        size,n,h,w=7,6,29,29
    else:
        size,n=((6,2),(8,4),(7,4),(8,4))[index%4]
        if size==6: h,w=rng.randint(17,23),rng.randint(20,28)
        elif size==8: h,w=rng.randint(28,29),rng.randint(28,29)
        else: h,w=rng.randint(24,29),rng.randint(24,29)
    m=size-2
    classes=list(range(6)) if n==6 else list(range(1,n+1))
    areas={4:{1:4,2:2},5:{0:0,1:9,2:6,3:3,4:4,5:5},6:{1:16,2:8,3:6,4:4}}[m]
    positive=[c for c in classes if c]
    # Vary the matching permutation per grid: a fixed cycle would let an agent
    # ignore the measured areas and merely advance the hole-count class.
    for _ in range(256):
        permutation=rng.sample(positive,len(positive))
        alt=dict(zip(positive,permutation))
        if all(alt[c]!=c and areas[alt[c]]>=c for c in positive): break
    else: return None
    if 0 in classes: alt[0]=0
    bg=rng.choice(list(range(1,10)) if n==6 else list(range(10)))
    available=[c for c in range(10) if c!=bg]
    bases=dict(zip(classes,rng.sample(available,n)))
    for _ in range(256):
        colors=dict(zip(classes,rng.sample(available,n)))
        if n==6 and 0 not in colors.values(): continue
        if all(bases[c] not in (colors[c],colors[alt[c]]) for c in classes): break
    else: return None
    nr,nc=(1,2) if n==2 else (2,2) if n==4 else (2,3)
    top,left=(0,0) if stress else (rng.randrange(3),rng.randrange(3))
    panel=(top,left,top+nr*size,left+nc*size)
    placements=[]
    if stress: placements.append((h-m,w-m,h,w))
    candidates=[(r,c,r+m,c+m) for r in range(h-m+1) for c in range(w-m+1)]
    rng.shuffle(candidates)
    for box in candidates:
        if _separated(box,panel) and all(_separated(box,old) for old in placements):
            placements.append(box)
            if len(placements)==n: break
    if len(placements)!=n: return None
    grid=[[bg]*w for _ in range(h)]
    tile_ids=rng.sample(classes,n); template_ids=rng.sample(classes,n)
    def stamp(r0,c0,side,color,holes):
        for r in range(side):
            for c in range(side):
                grid[r0+r][c0+c]=bg if (r-1,c-1) in holes else color
    for i,c in enumerate(tile_ids):
        holes=_regions(m,c,areas[alt[c]],rng)
        if holes is None: return None
        stamp(top+(i//nc)*size,left+(i%nc)*size,size,bases[c],holes)
    for box,c in zip(placements,template_ids):
        holes=_regions(m-2,c,areas[c],rng)
        if holes is None: return None
        stamp(box[0],box[1],m,colors[c],holes)
    # Orientation and position are independent of setting and query presentation.
    for _ in range(rng.randrange(4)): grid=[list(row) for row in _rotate(grid)]
    if rng.randrange(2): grid=[row[::-1] for row in grid]
    if background(grid)!=bg: return None
    return grid


def _make_input(seed,role,index,*,stress=False,offset=0):
    for attempt in range(offset,offset+512):
        grid=_candidate(seed,role,index,attempt,stress)
        if grid is not None:
            # Assertions are claims checked independently by protected Racket audits.
            for matching in SETTINGS: solve(grid,matching)
            return grid
    raise ValueError('bounded template sampler exhausted; no fallback is emitted')


@lru_cache(maxsize=64)
def _bank(seed):
    first=_make_input(seed,'train',0)
    for attempt in range(128):
        second=_make_input(seed,'train',1,offset=attempt*512)
        if all(any(rival_solve(g,matching,name)!=solve(g,matching) for g in (first,second))
               for matching in SETTINGS for name in rival_names(matching)):
            break
    else: raise ValueError('could not construct a distinguishing two-demo lesson')
    train=[first,second]+[_make_input(seed,'train',i) for i in range(2,6)]
    queries=[_make_input(seed,'query',i,stress=i==3) for i in range(4)]
    _rng(seed,'presentation').shuffle(queries)
    if len({str(g) for g in train+queries})!=10: raise ValueError('duplicate episode input')
    return train,queries


@lru_cache(maxsize=128)
def full_lesson(seed,matching):
    train,queries=_bank(seed)
    return {split:tuple((tuple(tuple(row) for row in g),tuple(tuple(row) for row in solve(g,matching)))
                       for g in grids) for split,grids in [('train',train),('test',queries)]}


def sample_input(seed,sample_index,difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in ('easy','medium','hard'): raise ValueError('unknown difficulty')
    return _make_input(seed,'production-'+difficulty,sample_index,stress=difficulty=='hard')
