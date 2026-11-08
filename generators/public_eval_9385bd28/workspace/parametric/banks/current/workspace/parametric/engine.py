"""Keyed rectangle composition and constructive matched-input sampler.

The public parent contains a two-column color key.  Each key row names a
source color and a fill color.  Rows are applied bottom-to-top.  All scene
objects of the source color define a bounding rectangle.  A zero or modal-
background fill restores the original rectangle (transparent composition);
otherwise the rectangle is painted and multiple disconnected source fragments
are restored on top.  A single solid source object is replaced.
"""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import json
import random

VALUES = ('combine_only', 'highlight_largest_change')
RIVALS = (
    'other_setting', 'top_to_bottom', 'literal_zero', 'overwrite_fragments',
    'first_mapping_only', 'highlight_smallest_change', 'raw_largest_box',
)
N4 = ((-1,0),(0,-1),(0,1),(1,0))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
        or not 1 <= len(g[0]) <= 30
        or any(type(row) is not list or len(row) != len(g[0])
               or any(type(v) is not int or not 0 <= v <= 9 for v in row)
               for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')


def components(cells):
    left = set(cells); out = []
    while left:
        start = min(left); left.remove(start); queue = [start]; found = {start}
        for r,c in queue:
            for dr,dc in N4:
                p = (r+dr,c+dc)
                if p in left:
                    left.remove(p); found.add(p); queue.append(p)
        out.append(sorted(found))
    return out


def bbox(cells):
    cells = list(cells)
    if not cells: raise ValueError('Cannot bound an empty cell set')
    return min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells)


def rect_cells(box):
    r0,c0,r1,c1 = box
    return [(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)]


def _background(g):
    counts = Counter(v for row in g for v in row)
    top = max(counts.values())
    winners = [v for v,n in counts.items() if n == top]
    if len(winners) != 1: raise ValueError('Expected a unique modal background')
    return winners[0]


def parse(g):
    grid_check(g); h,w = len(g),len(g[0]); bg = _background(g)
    mixed = components((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v != bg)
    candidates = []
    for group in mixed:
        r0,c0,r1,c1 = bbox(group)
        colors = {g[r][c] for r,c in group}
        if (c1-c0 == 1 and r1-r0+1 >= 2 and len(colors) >= 2
            and all(g[r][c0] != bg for r in range(r0,r1+1))):
            candidates.append((r1-r0+1, len(group), (r0,c0,r1,c1), group))
    if len(candidates) != 1:
        raise ValueError(f'Expected one connected two-column multicolor key, found {len(candidates)}')
    _,_,key_box,key_group = candidates[0]
    kr0,kc0,kr1,kc1 = key_box
    key_cells = set(rect_cells(key_box))
    entries = []
    seen_sources = set()
    for r in range(kr0,kr1+1):
        source,target = g[r][kc0],g[r][kc1]
        if source == bg: raise ValueError('Every key row needs a non-background source color')
        if source in seen_sources: raise ValueError('Key source colors must be unique')
        seen_sources.add(source)
        scene = [(rr,cc) for rr,row in enumerate(g) for cc,v in enumerate(row)
                 if v == source and (rr,cc) not in key_cells]
        comps = components(scene) if scene else []
        entries.append({'row':r,'source':source,'target':target,'cells':scene,
                        'components':comps,'bbox':bbox(scene) if scene else None})
    if not any(e['cells'] for e in entries): raise ValueError('Key does not refer to any scene object')
    return {'height':h,'width':w,'background':bg,'key_bbox':key_box,
            'key_cells':key_cells,'entries':entries}


def _compose(g, *, order='reverse', literal_zero=False, restore_fragments=True,
             first_only=False):
    p = parse(g); out = [row[:] for row in g]
    entries = list(reversed(p['entries'])) if order == 'reverse' else list(p['entries'])
    if first_only: entries = entries[:1]
    applied = []
    for entry in entries:
        if not entry['cells']: continue
        box = entry['bbox']; target = entry['target']; cells = rect_cells(box)
        transparent = target == p['background'] or (target == 0 and not literal_zero)
        if transparent:
            for r,c in cells: out[r][c] = g[r][c]
        else:
            for r,c in cells: out[r][c] = target
            if restore_fragments and len(entry['components']) >= 2:
                for r,c in entry['cells']: out[r][c] = entry['source']
        applied.append({**entry, 'transparent':transparent,
                        'bbox_area':(box[2]-box[0]+1)*(box[3]-box[1]+1)})
    changed = {(r,c) for r in range(p['height']) for c in range(p['width'])
               if (r,c) not in p['key_cells'] and out[r][c] != g[r][c]}
    return out,p,applied,components(changed) if changed else []


def _owner(component, out, operations):
    cells = set(component); scored = []
    for op in operations:
        if op['transparent']: continue
        box = op['bbox']
        score = sum(1 for r,c in cells
                    if box[0] <= r <= box[2] and box[1] <= c <= box[3]
                    and out[r][c] == op['target'])
        scored.append((score, -op['row'], op['source']))
    return max(scored)[2] if scored and max(scored)[0] else None


def analyze(g):
    out,p,ops,changed = _compose(g)
    raw = max((op for op in ops if not op['transparent']),
              key=lambda op:(op['bbox_area'],-op['row']), default=None)
    largest = max(changed, key=lambda cc:(len(cc),-cc[0][0],-cc[0][1]), default=[])
    return {'background':p['background'],'key_bbox':list(p['key_bbox']),
            'entries':[{'source':e['source'],'target':e['target'],'bbox':list(e['bbox']) if e['bbox'] else None,
                        'components':len(e['components'])} for e in p['entries']],
            'composed':out,'changed_component_sizes':[len(cc) for cc in changed],
            'largest_raw_operation':raw['source'] if raw else None,
            'largest_changed_component_owner':_owner(largest,out,ops),
            'largest_changed_cells':[list(x) for x in largest]}


def solve(g, value='combine_only', rival=None):
    if value not in VALUES: raise ValueError('Unknown finish setting')
    if rival is not None and rival not in RIVALS: raise ValueError('Unknown rival')
    if rival == 'other_setting':
        value = 'highlight_largest_change' if value == 'combine_only' else 'combine_only'
    order = 'top' if rival == 'top_to_bottom' else 'reverse'
    literal = rival == 'literal_zero'
    restore = rival != 'overwrite_fragments'
    first = rival == 'first_mapping_only'
    out,p,ops,changed = _compose(g, order=order, literal_zero=literal,
                                 restore_fragments=restore, first_only=first)
    highlight = value == 'highlight_largest_change' or rival in ('highlight_smallest_change','raw_largest_box')
    if not highlight: return out
    if rival == 'raw_largest_box':
        raw = max((op for op in ops if not op['transparent']),
                  key=lambda op:(op['bbox_area'],-op['row']), default=None)
        selected = [] if raw is None else [(r,c) for cc in changed for r,c in cc
                    if raw['bbox'][0] <= r <= raw['bbox'][2] and raw['bbox'][1] <= c <= raw['bbox'][3]]
    elif rival == 'highlight_smallest_change':
        selected = min(changed, key=lambda cc:(len(cc),cc[0]), default=[])
    else:
        selected = max(changed, key=lambda cc:(len(cc),-cc[0][0],-cc[0][1]), default=[])
    result = [row[:] for row in out]
    for r,c in selected: result[r][c] = 9
    return result


def self_check(g):
    try:
        p = parse(g)
        solve(g,'combine_only')
        if not any(len(e['components']) >= 2 for e in p['entries'] if e['cells']):
            return ['Expected at least one paired source-fragment mapping']
    except (ValueError,TypeError,IndexError) as exc:
        return [str(exc)]
    return []


def stream(seed, kind, index=0):
    integer(seed,0,2**63-1,'seed'); integer(index,0,2**63-1,'index')
    token = f'9385bd28:{seed}:{kind}:{index}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(token).digest(),'big'))


def _paint_l(g, box, color):
    r0,c0,r1,c1 = box
    for p in ((r0,c0),(r0,c0+1),(r0+1,c0),(r1,c1),(r1,c1-1),(r1-1,c1)):
        g[p[0]][p[1]] = color


def _candidate(seed,index,kind,h,w,attempt):
    rng = stream(seed,kind,index*257+attempt)
    bg = rng.choice((1,3,8))
    palette = [c for c in range(10) if c not in (0,9,bg)]
    rng.shuffle(palette)
    src_b,src_a,src_c,src_d,tgt_a,tgt_c,tgt_d = palette
    g = [[bg]*w for _ in range(h)]
    # Key: transparent cutter first, then raw-large rectangle, visible winner,
    # and a single-object replacement. Reverse application gives D,C,A,B.
    key_rows = [(src_b,0),(src_a,tgt_a),(src_c,tgt_c),(src_d,tgt_d)]
    kr = h-4; kc = 0
    for i,(s,t) in enumerate(key_rows): g[kr+i][kc]=s; g[kr+i][kc+1]=t

    # A is raw-largest on the left. B is a full-height transparent stripe that
    # splits A's produced change mask. C is smaller raw, larger visible component.
    ar0 = 1 + rng.randrange(2); ar1 = h-6-rng.randrange(2)
    ac0 = 3; ac1 = max(ac0+8, w//2)
    if ac1 >= w-10: ac1 = w-11
    aw = ac1-ac0+1
    bwidth = 3
    bc0 = ac0 + max(3,aw//2-1); bc1 = bc0+bwidth-1
    if bc1 >= ac1-2: bc0=ac0+3;bc1=bc0+2
    box_a=(ar0,ac0,ar1,ac1);box_b=(ar0,bc0,ar1,bc1)

    cr0 = ar0+2; cr1 = ar1-2
    cc0 = ac1+4; cc1 = w-3
    if cc1-cc0+1 < 5: raise ValueError('Canvas too narrow')
    box_c=(cr0,cc0,cr1,cc1)
    _paint_l(g,box_a,src_a); _paint_l(g,box_b,src_b); _paint_l(g,box_c,src_c)
    # One component is intentionally replaced rather than restored.
    dr = h-6; dc = w-5
    for r in (dr,dr+1):
        for c in (dc,dc+1): g[r][c]=src_d
    return g


def make_input(seed,index,kind='ordinary',stress=False):
    integer(seed,0,2**63-1,'seed'); integer(index,0,2**63-1,'index')
    if stress: h=w=30
    else:
        sizes=((20,28),(22,27),(19,29),(24,26),(26,28),(28,27))
        h,w=sizes[index % len(sizes)]
    for attempt in range(128):
        g=_candidate(seed,index,kind,h,w,attempt)
        try:
            info=analyze(g)
            if info['largest_raw_operation'] == info['largest_changed_component_owner']: continue
            if solve(g,'combine_only') == solve(g,'highlight_largest_change'): continue
            return g
        except (ValueError,IndexError):
            continue
    raise ValueError('Bounded keyed-composition sampler exhausted')


@lru_cache(maxsize=128)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed')
    demos=[make_input(seed,i,'demo') for i in range(6)]
    queries=[make_input(seed,i,'query',stress=i==3) for i in range(4)]
    packed=[json.dumps(g,separators=(',',':')) for g in demos+queries]
    if len(set(packed)) != len(packed): raise ValueError('Unexpected duplicate source input')
    # The first two demonstrations must reject every declared finite rival under
    # both settings without consulting held-out query labels.
    for value in VALUES:
        gold=[solve(g,value) for g in demos[:2]]
        for rival in RIVALS:
            if all(solve(g,value,rival=rival)==y for g,y in zip(demos[:2],gold)):
                raise ValueError(f'Teaching prefix failed to reject {value}/{rival}')
    return tuple(packed[:6]),tuple(packed[6:])
