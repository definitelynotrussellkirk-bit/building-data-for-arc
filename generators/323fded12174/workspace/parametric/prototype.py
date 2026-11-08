"""A separate matched-input family: occupancy or cue-color row ranking.

Python outputs are deterministic claims. The native worker/audit executes the
returned Racket program independently; generate never opens a Racket process.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
import hashlib
from pathlib import Path
import random

TASK_ID = '323fded12174'
VERSION = '1.0.0'
PARAMETERS = {'rank_by': ['occupancy', 'anchor_color']}
DEFAULT = {'rank_by': 'occupancy'}
MAX_TEACHING_ATTEMPTS = 128
MAX_NOVELTY_ATTEMPTS = 32

ANCHOR_PROGRAM = '''(rule!
  (let* ((occupancy (lambda (row) (count-where (lambda (v) (!= v 0)) row)))
         (anchor (first (sort g (lambda (a b) (> (occupancy a) (occupancy b))))))
         (colors (remove-duplicates (filter (lambda (v) (!= v 0)) anchor)))
         (target (first (sort colors
                   (lambda (a b)
                     (> (count-where (lambda (v) (= v a)) anchor)
                        (count-where (lambda (v) (= v b)) anchor)))))))
    (sort g (lambda (a b)
              (> (count-where (lambda (v) (= v target)) a)
                 (count-where (lambda (v) (= v target)) b))))))'''


def normalize_settings(settings):
    if not isinstance(settings, dict) or set(settings) != {'rank_by'}:
        raise ValueError('settings must contain exactly rank_by')
    mode = settings['rank_by']
    if type(mode) is not str or mode not in PARAMETERS['rank_by']:
        raise ValueError('rank_by must be occupancy or anchor_color')
    return {'rank_by': mode}


def program(settings):
    mode = normalize_settings(settings)['rank_by']
    if mode == 'occupancy':
        return Path(__file__).with_name('canonical.rkt').read_text()
    return ANCHOR_PROGRAM


def _occupancy(row):
    return sum(v != 0 for v in row)


def _mode(row, include_zero=False):
    counts = Counter(v for v in row if include_zero or v != 0)
    return min(counts, key=lambda c: (-counts[c], c))


def row_facts(grid):
    occupancies = [_occupancy(row) for row in grid]
    anchor_index = max(range(len(grid)), key=lambda i: occupancies[i])
    counts = Counter(v for v in grid[anchor_index] if v != 0)
    color = min(counts, key=lambda c: (-counts[c], c))
    return {'occupancies': occupancies, 'anchor_index': anchor_index,
            'anchor_color': color, 'anchor_counts': dict(counts),
            'target_counts': [row.count(color) for row in grid]}


def self_check(grid):
    if not isinstance(grid, (list, tuple)) or not 3 <= len(grid) <= 30:
        return ['height must be 3..30']
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ['rows must be sequences']
    width = len(grid[0])
    if not 5 <= width <= 30 or any(len(row) != width for row in grid):
        return ['width must be 5..30 and rows rectangular']
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ['cells must be literal integer colors 0..9']
    colors = {v for row in grid for v in row if v != 0}
    errors = []
    if len(colors) < 3:
        errors.append('at least three nonzero colors are required')
    occupancy = [_occupancy(row) for row in grid]
    if any(n == 0 or n == width for n in occupancy):
        errors.append('every row needs foreground and zero')
    if occupancy.count(max(occupancy)) != 1:
        errors.append('the maximum-occupancy anchor must be unique')
    anchor = grid[occupancy.index(max(occupancy))]
    counts = Counter(v for v in anchor if v != 0)
    if len(counts) < 2:
        errors.append('anchor needs at least two nonzero colors')
    if not counts or list(counts.values()).count(max(counts.values(), default=0)) != 1:
        errors.append('anchor must have a unique nonzero modal color')
    return errors


def occupancy_reference(grid):
    return [list(row) for row in sorted(grid, key=_occupancy, reverse=True)]


def anchor_color_reference(grid):
    color = row_facts(grid)['anchor_color']
    return [list(row) for row in sorted(grid, key=lambda row: row.count(color), reverse=True)]


def reference(grid, settings):
    mode = normalize_settings(settings)['rank_by']
    return occupancy_reference(grid) if mode == 'occupancy' else anchor_color_reference(grid)


# Finite sampler guard. The audit has an independent implementation and Racket
# programs, and independently decides which candidates fit demonstrations.
RIVALS = (
    'dominant_count', 'mixed_then_dominant', 'diversity_then_dominant',
    'ascending', 'first_row_anchor', 'last_row_anchor', 'dominant_anchor',
    'second_occupancy_anchor', 'global_color', 'anchor_first_color',
    'anchor_min_color', 'anchor_max_color', 'anchor_mode_including_zero',
    'presence', 'fraction', 'reverse_ties', 'lexicographic_ties',
    'occupancy_tiebreak', 'left_justify', 'sort_cells',
)
_CUE_RIVALS = set(RIVALS[4:13])


def rival_reference(grid, settings, name):
    mode = normalize_settings(settings)['rank_by']
    if name not in RIVALS:
        raise ValueError('unknown finite rival')
    facts = row_facts(grid)
    color = facts['anchor_color']
    anchor = grid[facts['anchor_index']]
    dominant = lambda row: max(Counter(v for v in row if v != 0).values())
    diversity = lambda row: len({v for v in row if v != 0})
    if mode == 'anchor_color':
        if name == 'first_row_anchor':
            color = _mode(grid[0])
        elif name == 'last_row_anchor':
            color = _mode(grid[-1])
        elif name == 'dominant_anchor':
            color = _mode(max(grid, key=dominant))
        elif name == 'second_occupancy_anchor':
            color = _mode(sorted(grid, key=_occupancy, reverse=True)[1])
        elif name == 'global_color':
            color = _mode([v for row in grid for v in row])
        elif name == 'anchor_first_color':
            color = next(v for v in anchor if v != 0)
        elif name == 'anchor_min_color':
            color = min(v for v in anchor if v != 0)
        elif name == 'anchor_max_color':
            color = max(anchor)
        elif name == 'anchor_mode_including_zero':
            color = _mode(anchor, include_zero=True)
    score = _occupancy if mode == 'occupancy' else lambda row: row.count(color)
    if name == 'dominant_count':
        key = dominant
    elif name == 'mixed_then_dominant':
        key = lambda row: (diversity(row) > 1, dominant(row))
    elif name == 'diversity_then_dominant':
        key = lambda row: (diversity(row), dominant(row))
    elif name == 'presence':
        key = lambda row: score(row) > 0
    elif name == 'fraction':
        key = lambda row: Fraction(score(row), len(row) if mode == 'occupancy' else _occupancy(row))
    else:
        key = score
    if name == 'reverse_ties':
        out = [row for i,row in sorted(enumerate(grid), key=lambda p: (-key(p[1]),-p[0]))]
    elif name == 'lexicographic_ties':
        out = sorted(grid, key=lambda row: (-key(row),tuple(row)))
    elif name == 'occupancy_tiebreak':
        out = sorted(grid, key=lambda row: (-key(row),-_occupancy(row)))
    else:
        out = sorted(grid, key=key, reverse=name != 'ascending')
    if name == 'left_justify':
        out = [[v for v in row if v != 0]+[0]*row.count(0) for row in out]
    elif name == 'sort_cells':
        out = [sorted(row) for row in out]
    return [list(row) for row in out]


def _active_rivals(mode):
    if mode == 'anchor_color':
        return RIVALS
    return tuple(n for n in RIVALS if n not in _CUE_RIVALS | {'fraction','occupancy_tiebreak'})


def teaching_survivors(grids, settings):
    mode = normalize_settings(settings)['rank_by']
    intended = [reference(g, settings) for g in grids]
    return [name for name in _active_rivals(mode)
            if all(rival_reference(g, settings, name) == out for g,out in zip(grids,intended))]


def _rng(seed, label, attempt=0):
    raw = f'{TASK_ID}:{VERSION}:{seed}:{label}:{attempt}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), 'big'))


def _render(counts, width, rng, first_color=None):
    values = [color for color,count in counts.items() for _ in range(count)]
    rng.shuffle(values)
    if first_color is not None:
        i=values.index(first_color)
        values[0],values[i]=values[i],values[0]
    n=len(values)
    layout=rng.randrange(3)
    if layout == 0:
        start=rng.randrange(width-n+1)
        positions=list(range(start,start+n))
    elif layout == 1:
        positions=sorted(rng.sample(range(width),n))
    else:
        positions=sorted(rng.sample(range(1,width-1),n-2)+[0,width-1]) if n>=2 and n<=width-1 else sorted(rng.sample(range(width),n))
    row=[0]*width
    for pos,value in zip(positions,values):
        row[pos]=value
    return row


def _core_scene(seed, role, attempt):
    rng=_rng(seed,f'core-{role}',attempt)
    m=rng.randint(3,6)
    palette=sorted(rng.sample(range(1,10),3))
    target=palette[(1,0,2)[role]]
    a,b=[c for c in palette if c != target]
    if rng.randrange(2):
        a,b=b,a
    anchor_n=3*m-2
    width=rng.randint(anchor_n+1,anchor_n+4) if role != 2 else rng.randint(anchor_n+m+1,min(30,anchor_n+m+5))
    rowspecs=[
        ('anchor',{target:m,a:m-1,b:m-1}),
        ('target_winner',{target:m+1,a:1}),
        ('other_mode',{a:3*m-3}),
        ('tie_small',{target:m-1,b:1}),
        ('tie_large',{target:m-1,b:m}),
        ('occupancy_tie',{target:1,a:m+1}),
        ('zero_target',{b:2,a:1}),
    ]
    extras=rng.randint(0,2)
    other_colors=[c for c in range(1,10) if c not in palette]
    rng.shuffle(other_colors)
    for i in range(extras):
        rowspecs.append((f'extra{i}',{other_colors[i]:rng.randint(1,anchor_n-2)}))
    rendered={name:_render(counts,width,rng,first_color=a if name=='anchor' else None)
              for name,counts in rowspecs}
    names=[name for name,_ in rowspecs if name != 'anchor']
    rng.shuffle(names)
    # Equal target scores must preserve the smaller-occupancy row first.
    i,j=names.index('tie_small'),names.index('tie_large')
    if i>j:
        names[i],names[j]=names[j],names[i]
    anchor_pos=(seed+2*role+attempt)%len(rowspecs)
    names.insert(anchor_pos,'anchor')
    return [rendered[name] for name in names]


def _random_scene(seed, label, height, width, attempt=0):
    rng=_rng(seed,label,attempt)
    ncolors=rng.randint(3,min(7,width-1))
    palette=rng.sample(range(1,10),ncolors)
    target=palette[0]
    anchor_n=width-1
    m=max(2,(anchor_n+ncolors-1)//ncolors+1)
    m=min(m,width-3)
    counts={target:m}
    remaining=anchor_n-m
    for color in palette[1:]:
        take=min(m-1,remaining)
        if take:
            counts[color]=take
            remaining-=take
    assert remaining==0
    specs=[counts,{target:m+1}]
    for i in range(height-2):
        occupancy=rng.randint(max(1,width//3),width-2)
        target_n=rng.randint(0,min(occupancy,m+3))
        count={target:target_n} if target_n else {}
        for _ in range(occupancy-target_n):
            color=rng.choice(palette[1:])
            count[color]=count.get(color,0)+1
        specs.append(count)
    # Even at the literal minimum, expose all three colors in the anchor.
    rows=[_render(count,width,rng) for count in specs]
    rng.shuffle(rows)
    return rows


def _input_bank(seed):
    for attempt in range(MAX_TEACHING_ATTEMPTS):
        core=[_core_scene(seed,role,attempt) for role in range(3)]
        if any(self_check(g) for g in core):
            continue
        if any(teaching_survivors(core,{'rank_by':mode}) for mode in PARAMETERS['rank_by']):
            continue
        if all(occupancy_reference(g)==anchor_color_reference(g) for g in core):
            continue
        break
    else:
        raise RuntimeError('bounded teaching construction exhausted')
    demos=list(core)
    seen={tuple(map(tuple,g)) for g in demos}
    shape_rng=_rng(seed,'shapes')
    demo_shapes=[(shape_rng.randint(4,7),shape_rng.randint(6,12)),
                 (shape_rng.randint(8,13),shape_rng.randint(11,19)),
                 (shape_rng.randint(14,20),shape_rng.randint(18,26))]
    small=(3,5) if seed==0 else (shape_rng.randint(3,6),shape_rng.randint(5,9))
    query_shapes=[small,(shape_rng.randint(8,14),shape_rng.randint(10,20)),
                  shape_rng.choice([(12,27),(24,12),(18,29),(26,17)]),(30,30)]
    novelty=[]
    queries=[]
    for category,shapes,destination in [('demo',demo_shapes,demos),('query',query_shapes,queries)]:
        for i,(height,width) in enumerate(shapes):
            for retry in range(MAX_NOVELTY_ATTEMPTS):
                g=_random_scene(seed,f'{category}-{i}',height,width,retry)
                fingerprint=tuple(map(tuple,g))
                if not self_check(g) and fingerprint not in seen and len(set(map(tuple,g)))==len(g):
                    break
            else:
                raise RuntimeError('bounded distinct-input construction exhausted')
            seen.add(fingerprint)
            destination.append(g)
            novelty.append(retry+1)
    return demos,queries,{'teaching_attempts':attempt+1,'novelty_attempts':novelty}


def generate(seed, settings, demos=3, queries=4):
    settings=normalize_settings(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('seed must be a literal integer in 0..2**63-1')
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError('demos must be an integer in 3..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an integer in 1..4')
    train_bank,test_bank,sampling=_input_bank(seed)
    pair=lambda g:{'input':[row[:] for row in g],'output':reference(g,settings)}
    return {'train':[pair(g) for g in train_bank[:demos]],
            'test':[pair(g) for g in test_bank[:queries]],
            'program_solution':program(settings),'settings':dict(settings),
            'sampling':sampling}
