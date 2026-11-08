"""Object-contact graph selection. Racket, not these claims, is label authority."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK = '8069b5294ce4'
SETTINGS = ('whole_cluster', 'two_hops')
CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
# Each motif is an induced grid graph; scaling preserves its contact edges.
MOTIFS = {
    'path7': ((0,0),(0,1),(0,2),(1,2),(2,2),(2,1),(2,0)),
    'path8': ((0,0),(0,1),(0,2),(0,3),(1,3),(2,3),(2,2),(2,1)),
    'branch6': ((0,1),(1,0),(1,1),(1,2),(2,1),(3,1)),
    'branch8': ((0,0),(1,0),(1,1),(1,2),(1,3),(2,1),(3,1),(3,2)),
    'ladder8': ((0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,2),(3,2)),
    'ring8': ((0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)),
}
RIVALS = ('whole_cluster', 'two_hops', 'one_hop', 'three_hops', 'exact_two',
          'all_objects', 'largest_area', 'path_by_count', 'color_order',
          'bfs_order', 'eight_contact', 'spatial_ball', 'global_colors')


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {'selection'}
            or settings['selection'] not in SETTINGS):
        raise ValueError('settings must contain only selection=whole_cluster|two_hops')
    return settings['selection']


def program(settings):
    mode = _setting(settings)
    text = (HERE / 'canonical.rkt').read_text(encoding='utf-8')
    if mode == 'whole_cluster':
        return text
    old = '(define cl (cluster-from g objs seed (range 0 (length objs))))'
    new = ('(define cl (remove-duplicates (append (list seed) (neighbors g objs seed) '
           '(flatmap (lambda (i) (neighbors g objs i)) (neighbors g objs seed)))))')
    if text.count(old) != 1:
        raise ValueError('selected canonical source changed; review the extension')
    return text.replace(old, new)


def counterfactual_program():
    text = program({'selection': 'two_hops'})
    return text.replace('(flatmap (lambda (i) (neighbors g objs i)) (neighbors g objs seed))', '(list)')


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30):
        raise ValueError('grid must be a 1..30 rectangular list')
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('grid requires exact ARC integers')


def analyze(grid, diagonal=False):
    """Independent Python BFS mirror for claims and finite adversarial checks."""
    _grid(grid)
    h, w = len(grid), len(grid[0])
    seen, objects, owner = set(), [], {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r,c) in seen:
                continue
            color, pending, cells = grid[r][c], [(r,c)], []
            seen.add((r,c))
            while pending:
                p = pending.pop()
                cells.append(p)
                for dr,dc in CARD:
                    q = (p[0]+dr,p[1]+dc)
                    if 0 <= q[0] < h and 0 <= q[1] < w and q not in seen and grid[q[0]][q[1]] == color:
                        seen.add(q)
                        pending.append(q)
            cells.sort()
            for p in cells: owner[p] = len(objects)
            objects.append({'color':color, 'cells':cells, 'top_left':cells[0]})
    blue = [i for i,obj in enumerate(objects) if obj['color'] == 1]
    if len(blue) != 1: raise ValueError('exactly one blue object required')
    edges = [set() for _ in objects]
    dirs = tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c) if diagonal else CARD
    for (r,c),i in owner.items():
        for dr,dc in dirs:
            j = owner.get((r+dr,c+dc))
            if j is not None and j != i: edges[i].add(j)
    distances = {blue[0]:0}
    queue = deque([blue[0]])
    while queue:
        i = queue.popleft()
        for j in sorted(edges[i]):
            if j not in distances:
                distances[j] = distances[i]+1
                queue.append(j)
    return {'objects':objects, 'edges':edges, 'seed':blue[0], 'distances':distances}


def claim(grid, mode, *, intended='two_hops'):
    info = analyze(grid, diagonal=(mode == 'eight_contact'))
    objs, edges, dist = info['objects'],info['edges'],info['distances']
    base = intended if mode not in SETTINGS else mode
    ids = sorted(i for i in dist if base == 'whole_cluster' or dist[i] <= 2)
    if mode in ('one_hop','three_hops','exact_two'):
        radius = {'one_hop':1,'three_hops':3,'exact_two':2}[mode]
        ids = sorted(i for i in dist if (dist[i] == radius if mode == 'exact_two' else dist[i] <= radius))
    elif mode == 'all_objects': ids = list(range(len(objs)))
    elif mode == 'largest_area':
        unseen, groups = set(range(len(objs))), []
        while unseen:
            group, queue = set(), [min(unseen)]
            while queue:
                i = queue.pop()
                if i in group: continue
                group.add(i); unseen.discard(i)
                queue.extend(edges[i]-group)
            groups.append(group)
        ids = sorted(max(groups, key=lambda g: (sum(len(objs[i]['cells']) for i in g), -min(g))))
    elif mode == 'color_order': ids.sort(key=lambda i: (objs[i]['color'],objs[i]['top_left']))
    elif mode == 'bfs_order': ids.sort(key=lambda i: (dist[i],objs[i]['top_left']))
    elif mode == 'spatial_ball':
        p = objs[info['seed']]['top_left']
        ids = [i for i in dist if sum(abs(a-b) for a,b in zip(objs[i]['top_left'],p)) <= 2]
    elif mode == 'global_colors':
        colors = sorted({objs[i]['color'] for i in ids})
        links = {(objs[i]['color'],objs[j]['color']) for i,e in enumerate(edges) for j in e}
        return [[1 if a == b else 8 if (a,b) in links else 0 for b in colors] for a in colors]
    if not ids: return [[0]]  # A total rival; empty selection is an explicit null answer.
    if mode == 'path_by_count':
        return [[1 if r == c else 8 if abs(r-c) == 1 else 0 for c in range(len(ids))] for r in range(len(ids))]
    return [[1 if i == j else 8 if j in edges[i] else 0 for j in ids] for i in ids]


def _rng(seed, stream):
    return random.Random(int.from_bytes(hashlib.sha256(f'{TASK}:v1:{seed}:{stream}'.encode()).digest(),'big'))


def _orient(cells, turns, reflect):
    transformed = []
    for r,c in cells:
        if reflect: c = -c
        for _ in range(turns): r,c = c,-r
        transformed.append((r,c))
    r0,c0 = min(r for r,c in transformed),min(c for r,c in transformed)
    return [(r-r0,c-c0) for r,c in transformed]


def _scene(seed, stream, motif, root, h, w, boundary=False):
    rng = _rng(seed, stream)
    cells = _orient(MOTIFS[motif],rng.randrange(4),bool(rng.randrange(2)))
    mh,mw = max(r for r,c in cells)+1,max(c for r,c in cells)+1
    decoy_w = 5 if w >= 17 else 3
    available = w-decoy_w-1
    if boundary:
        rows = [i*h//mh for i in range(mh+1)]
        cols = [i*available//mw for i in range(mw+1)]
        r0 = c0 = 0
    else:
        th = min(rng.choice((2,2,3,4)),h//mh)
        tw = min(rng.choice((2,2,3,4)),available//mw)
        if stream == 'demo:0':
            th = tw = 2  # 28 selected cells versus a 50-cell non-blue component.
        rows = [i*th for i in range(mh+1)]
        cols = [i*tw for i in range(mw+1)]
        r0,c0 = rng.randrange(h-rows[-1]+1),rng.randrange(available-cols[-1]+1)
    palette = rng.sample(list(range(2,10)), len(cells)-1)
    colors = palette[:root]+[1]+palette[root:]
    grid = [[0]*w for _ in range(h)]
    for i,(mr,mc) in enumerate(cells):
        ra,rb,ca,cb = r0+rows[mr],r0+rows[mr+1],c0+cols[mc],c0+cols[mc+1]
        for r in range(ra,rb):
            for c in range(ca,cb): grid[r][c] = colors[i]
        # Preserve ports and connectivity while varying multi-cell silhouettes.
        if rb-ra >= 3 and cb-ca >= 3:
            for r,c in ((ra,ca),(ra,cb-1),(rb-1,ca),(rb-1,cb-1)):
                if rng.random() < .45: grid[r][c] = 0
    decoys = rng.sample(palette,2)
    split = rng.randrange(1,h)
    for r in range(h):
        for c in range(w-decoy_w,w): grid[r][c] = decoys[int(r >= split)]
    if rng.randrange(2): grid = [row[::-1] for row in grid]
    return grid


def generate(seed, settings, demos=3, queries=4):
    mode = _setting(settings)
    if type(seed) is not int or seed < 0: raise ValueError('seed must be a nonnegative exact integer')
    if type(demos) is not int or not 2 <= demos <= 6: raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1 <= queries <= 4: raise ValueError('queries must be 1..4')
    demo_specs = [('path7',0,10,17),('ladder8',1,12,18),('branch6',0,8,13),
                  ('ring8',3,14,19),('branch8',5,16,22),('path8',3,18,24)]
    query_specs = [('path8',0,8,13),('branch8',0,17,23),('ring8',5,24,21),('ladder8',1,30,30)]
    def pair(spec,stream,boundary=False):
        g = _scene(seed,stream,*spec,boundary=boundary)
        return {'input':g, 'output':claim(g,mode)}
    return {'train':[pair(s,f'demo:{i}') for i,s in enumerate(demo_specs[:demos])],
            'test':[pair(s,f'query:{i}',i == 3) for i,s in enumerate(query_specs[:queries])],
            'program_solution':program(settings), 'settings':dict(settings)}


def teaching_check(episode):
    """Fit only demonstrations; report surviving rivals with query disagreement."""
    mode = _setting(episode['settings'])
    findings = []
    for rival in RIVALS:
        if rival == mode: continue
        fits = all(claim(p['input'],rival,intended=mode) == p['output'] for p in episode['train'])
        if fits:
            bad = [i for i,p in enumerate(episode['test']) if claim(p['input'],rival,intended=mode) != p['output']]
            if bad: findings.append({'rival':rival,'queries':bad})
    return findings


def public_turn(episode, index=0):
    if type(index) is not int or not 0 <= index < len(episode['test']):
        raise ValueError('query index out of range')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][index]['input']}]})
