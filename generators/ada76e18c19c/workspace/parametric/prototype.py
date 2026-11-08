"""Separate native family: exact row fill, optionally followed by global color selection.

Python outputs are claims. Native qualification independently executes every label.
The production generator and exact canonical source are not modified.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ('all_colors', 'filled_majority')
FILL_POLICIES = ('exact', 'any_two', 'same_many', 'per_color', 'endpoints', 'none')
SELECTORS = ('all', 'post', 'pre', 'least', 'min_color', 'max_color', 'first', 'last',
             'longest_row', 'largest_component', 'component_only', 'row_frequency')
POLICIES = tuple(dict.fromkeys(
    [f'{f}/{s}' for f in FILL_POLICIES for s in ('all','post')]
    + [f'exact/{s}' for s in SELECTORS]
))


def _int(name, value, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an integer in [{lo}, {hi}]')


def _settings(settings):
    if not isinstance(settings, dict) or set(settings) != {'mode'} or settings['mode'] not in MODES:
        raise ValueError('settings must contain exactly one supported mode')
    return settings['mode']


def _grid(g):
    if (not isinstance(g, list) or not 1 <= len(g) <= 30 or
        not isinstance(g[0], list) or not 1 <= len(g[0]) <= 30 or
        any(not isinstance(row, list) or len(row) != len(g[0]) for row in g) or
        any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row)):
        raise ValueError('expected a rectangular ARC grid bounded by 30x30')


def fill(g, policy='exact'):
    out = deepcopy(g)
    for r, row in enumerate(g):
        cells = [(c,v) for c,v in enumerate(row) if v]
        if not cells or policy == 'none':
            continue
        colors = {v for _,v in cells}
        groups = []
        if policy == 'exact' and len(cells) == 2 and len(colors) == 1:
            groups = [(cells[0][0],cells[-1][0],cells[0][1])]
        elif policy == 'any_two' and len(cells) == 2:
            groups = [(cells[0][0],cells[-1][0],cells[0][1])]
        elif policy == 'same_many' and len(cells) >= 2 and len(colors) == 1:
            groups = [(cells[0][0],cells[-1][0],cells[0][1])]
        elif policy == 'endpoints' and len(cells) >= 2 and cells[0][1] == cells[-1][1]:
            groups = [(cells[0][0],cells[-1][0],cells[0][1])]
        elif policy == 'per_color':
            for color in dict.fromkeys(v for _,v in cells):
                cs = [c for c,v in cells if v == color]
                if len(cs) == 2:
                    groups.append((cs[0],cs[1],color))
        for lo,hi,color in groups:
            out[r][lo:hi+1] = [color]*(hi-lo+1)
    return out


def components(g):
    seen, groups = set(), []
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if not color or (r,c) in seen:
                continue
            stack, group = [(r,c)], []
            seen.add((r,c))
            while stack:
                rr,cc = stack.pop(); group.append((rr,cc))
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr,nc=rr+dr,cc+dc
                    if (0 <= nr < len(g) and 0 <= nc < len(row) and
                        (nr,nc) not in seen and g[nr][nc] == color):
                        seen.add((nr,nc)); stack.append((nr,nc))
            groups.append((color,group))
    return groups


def winner(g):
    """Global count, with first row-major occurrence breaking ties."""
    counts = Counter(v for row in g for v in row if v)
    return max(counts, key=counts.get) if counts else 0


def predict(g, policy):
    f, selector = policy.split('/')
    if f not in FILL_POLICIES or selector not in SELECTORS:
        raise ValueError(f'unknown policy {policy}')
    out = fill(g,f)
    if selector == 'all':
        return out
    colors = list(dict.fromkeys(v for row in out for v in row if v))
    if not colors:
        return out
    if selector == 'post': color = winner(out)
    elif selector == 'pre': color = winner(g)
    elif selector == 'least':
        counts = Counter(v for row in out for v in row if v)
        color = min(colors, key=counts.get)
    elif selector == 'min_color': color = min(colors)
    elif selector == 'max_color': color = max(colors)
    elif selector == 'first': color = colors[0]
    elif selector == 'last': color = colors[-1]
    elif selector == 'row_frequency':
        counts = Counter(row[next(c for c,v in enumerate(row) if v)]
                         for row in g if len([v for v in row if v]) == 2
                         and len({v for v in row if v}) == 1)
        color = max(colors, key=lambda c:counts[c])
    elif selector == 'longest_row':
        row = max(out, key=lambda row:sum(v!=0 for v in row))
        color = next(v for v in row if v)
    else:
        color, cells = max(components(out), key=lambda x:len(x[1]))
        if selector == 'component_only':
            cells = set(cells)
            return [[v if (r,c) in cells else 0 for c,v in enumerate(row)]
                    for r,row in enumerate(out)]
    return [[v if v == color else 0 for v in row] for row in out]


def solve(g, mode):
    _grid(g)
    if mode not in MODES: raise ValueError('unsupported mode')
    return predict(g, 'exact/all' if mode == 'all_colors' else 'exact/post')


def program(settings):
    mode = _settings(settings)
    return (HOME / ('canonical.rkt' if mode == 'all_colors' else 'filled_majority.rkt')).read_text()


def _lesson(seed, index):
    """Three complementary counterexamples: same-many, blocked-pair, mismatched pair.

    The largest post-fill color has two separated shorter rows. A different
    pre-fill leader has a longer single row and a long negative row. Incorrect
    relaxation of the negative row changes the post-fill winner.
    """
    rng = random.Random(f'row-fill/lesson/{seed}/{index}')
    palette = random.Random(f'row-fill/palette/{seed}').sample(range(1,10),3)
    a,b,c = [palette[(index+j)%3] for j in range(3)]
    width = rng.randint(13,17)
    height = rng.randint(9,13)
    g = [[0]*width for _ in range(height)]
    b_len = rng.randint(7, width-4)
    a_len1 = rng.randint(5,b_len-1)
    a_len2 = b_len+4-a_len1
    # Ordered semantic rows are separated so a color-union is not a component.
    rs = sorted(rng.sample(range(height),6))
    positives = ((rs[0],a_len1,a),(rs[1],b_len,b),(rs[2],a_len2,a),(rs[3],4,c))
    if index % 3 == 1:
        # One long A row beats two short B rows plus B's blocked pair. This
        # breaks the shortcut that counts qualifying rows rather than cells.
        positives = ((rs[0],width-1,a),(rs[1],4,b),(rs[2],4,b),(rs[3],4,c))
    for r,length,col in positives:
        start=rng.randrange(width-length+1)
        g[r][start]=g[r][start+length-1]=col
    lo,hi=0,width-1
    neg=rs[4]
    kind=index%3
    if kind == 0:
        for col in (lo,width//2,hi): g[neg][col]=b
    elif kind == 1:
        g[neg][lo]=g[neg][hi]=b; g[neg][width//2]=c
    else:
        g[neg][lo]=b; g[neg][hi]=c
    # A nonwinning isolated cue defeats 'select just a single filled row'.
    g[rs[5]][rng.randrange(width)] = c
    if index % 2: g.reverse()
    if rng.randrange(2): g=[list(reversed(row)) for row in g]
    return g


def _query(seed,index):
    rng = random.Random(f'row-fill/query/{seed}/{index}')
    h,w=((10,15),(16,19),(23,26),(30,30))[index]
    palette = rng.sample(range(1,10), rng.randint(3,6))
    for attempt in range(64):
        g=[]
        for r in range(h):
            row=[0]*w
            kind=(r+attempt)%6
            a,b=rng.sample(palette,2)
            lo,hi=sorted(rng.sample(range(w),2))
            if r in (0,h-1) or kind in (0,1):
                if r in (0,h-1): lo,hi=0,w-1
                row[lo]=row[hi]=a
            elif kind==2:
                for col in rng.sample(range(w),3): row[col]=a
            elif kind==3:
                lo,mid,hi=sorted(rng.sample(range(w),3))
                row[lo]=row[hi]=a;row[mid]=b
            elif kind==4:
                row[lo],row[hi]=a,b
            else:
                for col in rng.sample(range(w), rng.randint(8 if w == 30 else 6,min(12,w))):
                    row[col]=rng.choice(palette)
            g.append(row)
        filled=fill(g)
        counts=Counter(v for row in filled for v in row if v)
        best=sorted(counts.values(),reverse=True)
        if len(best)>1 and best[0]>best[1] and filled!=g:
            return g
    raise ValueError('bounded query construction could not produce unique post-fill mode')


def generate(seed, settings, demos, queries):
    mode = _settings(settings)
    _int('seed',seed,0,2**63-1);_int('demos',demos,3,6);_int('queries',queries,1,4)
    train=[_lesson(seed,i) for i in range(demos)]
    test=[_query(seed,i) for i in range(4)]
    if len({repr(g) for g in train+test}) != len(train)+4:
        raise ValueError('duplicate episode input')
    return {'train':[{'input':g,'output':solve(g,mode)} for g in train],
            'test':[{'input':g,'output':solve(g,mode)} for g in test[:queries]],
            'program_solution':program(settings)}


def teaching_check(episode):
    """Fit each policy to demonstrations alone; query labels only audit survivors."""
    survivors=[];failures=[]
    for policy in POLICIES:
        if all(predict(pair['input'],policy)==pair['output'] for pair in episode['train']):
            survivors.append(policy)
            bad=[i for i,pair in enumerate(episode['test']) if predict(pair['input'],policy)!=pair['output']]
            if bad: failures.append({'policy':policy,'queries':bad})
    return {'policies':len(POLICIES),'survivors':survivors,'failures':failures}


def public_turn(episode, query_index):
    _int('query_index',query_index,0,len(episode['test'])-1)
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][query_index]['input'])}]}


def racket_policy(fill_mode='exact', selector='post'):
    """Standalone executed rival used by audits, not a source of gold claims."""
    if fill_mode not in ('exact','any_two','same_many','endpoints','none') or selector not in ('all','post','pre','first','last','min_color','max_color','row_frequency'):
        raise ValueError('only the explicit bounded Racket rival subset is supported')
    gate={
        'exact':'(and (= (length vals) 2) (= (length colors) 1))',
        'any_two':'(= (length vals) 2)',
        'same_many':'(and (>= (length vals) 2) (= (length colors) 1))',
        'endpoints':'(and (>= (length vals) 2) (= (first vals) (last vals)))',
        'none':'#f',
    }[fill_mode]
    filled=f'''(grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (let* ((row (row-at g r))
               (vals (filter (lambda (v) (not (= v 0))) row))
               (colors (remove-duplicates vals))
               (cs (filter (lambda (cc) (not (= (at g r cc) 0))) (range (cols g)))))
          (if {gate}
              (if (and (>= c (first cs)) (<= c (last cs))) (first vals) (at g r c))
              (at g r c)))))'''
    if selector=='all': result='filled'
    else:
        source='g' if selector=='pre' else 'filled'
        choose = {'first':'(first colors)', 'last':'(last colors)',
                  'min_color':'(apply min colors)', 'max_color':'(apply max colors)'}.get(
                      selector, '(pick-max colors (lambda (color) (count-color source color)))')
        if selector == 'row_frequency':
            choose = '''(pick-max colors (lambda (color)
              (count-if (lambda (row)
                (let* ((vals (filter (lambda (v) (not (= v 0))) row)))
                  (and (= (length vals) 2) (= (first vals) color) (= (second vals) color)))) g)))'''
        result=f'''(let* ((source {source})
                 (colors (remove-duplicates (filter (lambda (v) (not (= v 0))) (apply append source)))))
            (if (null? colors) filled
                (let* ((selected {choose}))
                  (grid-from-fn (rows filled) (cols filled)
                    (lambda (r c) (if (= (at filled r c) selected) selected 0))))))'''
    return f'(rule! (lambda (g) (let* ((filled {filled})) {result})))\n'
