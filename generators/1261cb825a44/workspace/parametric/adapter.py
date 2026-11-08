"""Native source-bound corner-key crop family; only claimed labels in Python.

`isolated` is the canonical rule, byte for byte. `context` retains every interior
pixel inside the bounding box of the CORNER-KEY-COLORED non-corner cells rather
than painting only selected pixels. The bounding box is always determined by
those selected cells, not by distractors, overall nonbackground content, or a
fixed crop. Input sampling is independent of the chosen setting.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import canonical_path, find_root

ID = '1261cb825a44'
ROOT = find_root(__file__)
VIEWS = ('isolated', 'context')
PROFILES_DEMO = ((12, 15), (18, 20), (10, 12), (24, 26), (13, 17), (30, 30))
PROFILES_QUERY = ((9, 10), (16, 19), (25, 27), (30, 30))


def _strict_int(v, name, low, high):
    if type(v) is not int or not low <= v <= high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')


def _view(settings):
    if type(settings) is not dict or set(settings) != {'view'} or settings['view'] not in VIEWS:
        raise ValueError('settings must contain only view=isolated|context')
    if type(settings['view']) is not str:
        raise ValueError('view must be a string')
    return settings['view']


@lru_cache(maxsize=1)
def canonical():
    programs = set()
    for line in canonical_path(ROOT).read_text(encoding='utf-8').splitlines():
        if line.strip():
            obj = json.loads(line)
            if obj.get('task_id') == ID:
                programs.add(obj['program_solution'])
    if len(programs) != 1:
        raise ValueError('unique, present canonical rule required')
    return programs.pop()


def program(settings):
    source = canonical()
    if _view(settings) == 'isolated':
        return source
    original = '(cells->grid cells key-color)'
    if source.count(original) != 1:
        raise ValueError('canonical crop operation changed: cannot rewrite safely')
    # The key's own corner glyph is metadata, NEVER image content. Clearing all
    # corners before cropping prevents contamination even in adversarial inputs.
    alternative = ('(let* ((bb (bbox-of-cells cells)) '
                   '(without-keys (recolor-cells g corners 0))) '
                   '(subgrid without-keys (first bb) (second bb) '
                   '(third bb) (fourth bb)))')
    return source.replace(original, alternative)


def _rng(seed, role, index):
    digest = hashlib.sha256(f'corner-key-family-v3|{seed}|{role}|{index}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _corners(h, w):
    return [(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)]


def _select_box(rng, h, w, dense_profile):
    """Choose an input-dependent nontrivial bbox, including near-boundaries."""
    min_h, min_w = 5, 5
    if h == 30:
        min_h = 20
    if w >= 27:
        min_w = 19
    if dense_profile:
        min_h = max(min_h, round(0.74*h))
        min_w = max(min_w, round(0.74*w))
    for _ in range(160):
        sh = rng.randint(min_h, h-1)
        sw = rng.randint(min_w, w-1)
        # Shift the bounds, including zero and the final legal offset.
        r0 = rng.randint(0, h-sh)
        c0 = rng.randint(0, w-sw)
        r1, c1 = r0+sh-1, c0+sw-1
        if (r0,c0) not in _corners(h,w) and (r1,c1) not in _corners(h,w):
            return r0,c0,r1,c1
    raise RuntimeError('box selection failed')


def _connected_path(rng, box):
    r0,c0,r1,c1=box
    moves = [(1,0)]*(r1-r0)+[(0,1)]*(c1-c0)
    rng.shuffle(moves)
    r,c=r0,c0
    cells={(r,c)}
    for dr,dc in moves:
        r+=dr;c+=dc;cells.add((r,c))
    return cells


def _scene(seed, role, index, shape, *, corner_phase=0):
    h,w=shape
    rng=_rng(seed,role,index)
    assert 9 <= h <= 30 and 10 <= w <= 30
    box=_select_box(rng,h,w,index%2==0)
    r0,c0,r1,c1=box
    g=[[0]*w for _ in range(h)]
    key,inner,outer=rng.sample(range(1,10),3)
    corner=_corners(h,w)[(corner_phase+index) % 4]
    g[corner[0]][corner[1]]=key

    # One irregular FOUR-CONNECTED key object always reaches both extremes of
    # its OWN variable bounding box. Arbitrary nonkey objects cannot determine
    # this intermediate: B must first identify key via the unique corner.
    occupied=_connected_path(rng,box)
    target=min((r1-r0+1)*(c1-c0+1)-6,
               max(len(occupied), int((r1-r0+1)*(c1-c0+1)*
                   (0.17 if index%2==0 else 0.58))))
    forbidden = set(_corners(h,w))
    def neighbors(p):
        r,c=p
        return ((r+dr,c+dc) for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)))
    frontier={p for q in occupied for p in neighbors(q)
              if r0<=p[0]<=r1 and c0<=p[1]<=c1 and p not in occupied and p not in forbidden}
    while len(occupied)<target and frontier:
        new=rng.choice(sorted(frontier))
        frontier.remove(new)
        occupied.add(new)
        for p in neighbors(new):
            if r0<=p[0]<=r1 and c0<=p[1]<=c1 and p not in occupied and p not in forbidden:
                frontier.add(p)
    assert (r0,c0) in occupied and (r1,c1) in occupied
    for r,c in occupied:
        g[r][c]=key

    # An embedded, different-color set guarantees two genuinely different
    # rule predictions; unrelated external distractors refute crop-all-colors.
    free=[(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if not g[r][c] and (r,c) not in _corners(h,w)]
    inside_count=min(len(free),max(3,len(free)//(4 if index%2==0 else 9)))
    if inside_count<3:
        raise RuntimeError('insufficient space for embedded teaching controls')
    rng.shuffle(free)
    for j,(r,c) in enumerate(free[:inside_count]):
        g[r][c]=inner if (j%4) else outer

    outside=[(r,c) for r in range(h) for c in range(w)
             if not(r0<=r<=r1 and c0<=c<=c1) and (r,c) not in _corners(h,w)]
    rng.shuffle(outside)
    # High/low outside density crossed with small/large key occupancy.
    outside_count=min(len(outside),max(3,round(len(outside)*(0.68 if index%2==0 else 0.10))))
    for j,(r,c) in enumerate(outside[:outside_count]):
        g[r][c] = inner if j%3 else outer
    return g


def _key_and_crop(g):
    h,w=len(g),len(g[0]); cs=set(_corners(h,w))
    markers=[(r,c) for r,c in cs if g[r][c]]
    if len(markers)!=1:
        raise ValueError('requires exactly one nonbackground corner')
    key=g[markers[0][0]][markers[0][1]]
    kept=[(r,c) for r,row in enumerate(g) for c,val in enumerate(row) if val==key and (r,c) not in cs]
    if not kept:
        raise ValueError('requires an interior key-colored payload')
    r0=min(r for r,c in kept);r1=max(r for r,c in kept)
    c0=min(c for r,c in kept);c1=max(c for r,c in kept)
    return (key,set(kept),(r0,c0,r1,c1))


def transform(g, view):
    if view not in VIEWS:
        raise ValueError('unknown view')
    key,cells,(r0,c0,r1,c1)=_key_and_crop(g)
    corner_set=set(_corners(len(g),len(g[0])))
    if view=='isolated':
        return [[key if (r,c) in cells else 0 for c in range(c0,c1+1)]
                for r in range(r0,r1+1)]
    return [[0 if (r,c) in corner_set else g[r][c] for c in range(c0,c1+1)]
            for r in range(r0,r1+1)]


def generate(seed, settings, demos=3, queries=4):
    _strict_int(seed,'seed',0,2**63-1)
    _strict_int(demos,'demos',2,6)
    _strict_int(queries,'queries',4,4)
    view=_view(settings)
    corner_phase=_rng(seed,'corner',0).randrange(4)
    seen=set()
    train=[];test=[]
    for role,count,profiles,destination in (
        ('demo',demos,PROFILES_DEMO,train),('query',queries,PROFILES_QUERY,test)):
        for i in range(count):
            g=_scene(seed,role,i,profiles[i],corner_phase=corner_phase)
            key=json.dumps(g,separators=(',',':'))
            if key in seen:
                raise ValueError('repeated input')
            seen.add(key)
            destination.append({'input':g,'output':transform(g,view)})
    return {'train':train,'test':test,'program_solution':program(settings)}


def predict_rivals(g):
    """Finite bypass bank used by the author's self-review, never exported."""
    from collections import Counter
    key,cells,(r0,c0,r1,c1)=_key_and_crop(g)
    h,w=len(g),len(g[0]); corners=set(_corners(h,w))
    isolated=transform(g,'isolated')
    contextual=transform(g,'context')
    def maskcrop(cel, value):
        rr=[r for r,c in cel];cc=[c for r,c in cel]
        if not rr:return [[0]]
        return [[value if (r,c) in cel else 0 for c in range(min(cc),max(cc)+1)]
                for r in range(min(rr),max(rr)+1)]
    nonbg=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v]
    cols=Counter(v for row in g for v in row if v)
    majority=max(cols,key=cols.get)
    minority=min(cols,key=cols.get)
    return {
        'isolated':isolated,
        'context':contextual,
        'include_corner':maskcrop(cells|{(r,c) for r,c in corners if g[r][c]},key),
        'bbox_all_nonzero':[[g[r][c] for c in range(min(c for r,c in nonbg),max(c for r,c in nonbg)+1)] for r in range(min(r for r,c in nonbg),max(r for r,c in nonbg)+1)],
        'majority_color':maskcrop({(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==majority and (r,c) not in corners},majority),
        'minority_color':maskcrop({(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==minority and (r,c) not in corners},minority),
        'keep_full_input':g,
        'crop_other_colors':maskcrop({(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v not in (0,key) and (r,c) not in corners},1),
        'fixed_bbox_from_center':[[g[r][c] for c in range(max(0,w//4),min(w,3*w//4))] for r in range(max(0,h//4),min(h,3*h//4))],
    }


def lesson_check(train,test):
    """Reject every finite rival fitting demos but diverging on a future query."""
    banks=[predict_rivals(p['input']) for p in train]
    fits=[name for name in banks[0] if all(bank[name]==p['output'] for bank,p in zip(banks,train))]
    if len(fits)!=1 or fits[0] not in VIEWS:
        raise ValueError(f'minimum lesson underidentified against declared rivals: {fits}')
    other=next(v for v in VIEWS if v!=fits[0])
    if not any((bank:=predict_rivals(p['input']))[fits[0]]!=bank[other] for p in test):
        raise ValueError('query bank cannot distinguish the two settings')
    return {'survivors': fits, 'rivals_checked': len(banks[0]),
            'queries': len(test), 'scope':'finite declared bypasses, not universal uniqueness'}
