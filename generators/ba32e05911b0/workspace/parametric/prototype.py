"""Proposed left/right rolling ladders; canonical authority stays untouched.

Python outputs are claims until the protected Racket worker re-executes them.
Input draws are independent of the episode's private direction setting.
"""
from __future__ import annotations
import copy
import hashlib
import json
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIRECTIONS = ('right', 'left')
SHORTCUTS = ('straight', 'one_roll', 'ignore_blocks', 'ignore_edge',
             'reset_column', 'first_marker_only', 'cap_two',
             'roll_cap_2', 'roll_cap_3', 'roll_cap_4', 'roll_cap_5')


def _settings(value):
    if type(value) is not dict or set(value) != {'direction'} or value['direction'] not in DIRECTIONS:
        raise ValueError('settings must contain exactly direction=right or direction=left')
    return value['direction']


def program(settings):
    direction = _settings(settings)
    source = (BASE / 'canonical.rkt').read_text(encoding='utf-8')
    if direction == 'right':
        return source
    # The resource is exactly `(rule! <lambda>)`. Retain that complete lambda;
    # reflection changes the movement direction, not colors or collision logic.
    inner = source[len('(rule! '):-1]
    return '(rule! (lambda (g) (flip-lr (' + inner + ' (flip-lr g)))))'


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('expected a nonempty grid of size at most 30x30')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or any(type(v) is not int or v not in (0,6,7) for v in row) for row in grid):
        raise ValueError('expected rectangular exact-integer input colors 0,6,7')


def _right(grid, mode=None):
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    markers = [(r,c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    if mode == 'first_marker_only':
        markers = markers[:1]
    traces = []
    roll_limit = 1 if mode == 'one_roll' else (int(mode[-1]) if mode and mode.startswith('roll_cap_') else None)
    for mr, mc in markers:
        r, c, rolls = mr-1, mc, 0
        events = []
        while r >= 0:
            if grid[r][c] != 7 or mode == 'straight':
                out[r][c] = 2
                r -= 1
                continue
            end = c
            while end+1 < w and grid[r][end+1] == 7:
                end += 1
            if mode == 'cap_two':
                end = min(end, c+1)
            nxt = end+1
            if nxt == w:
                if mode == 'ignore_edge':
                    out[r][c] = 2
                    r -= 1
                    continue
                out[r+1][c] = 6
                events.append({'kind':'edge_stop', 'row':r, 'col':c, 'run_end':end})
                break
            blocked = any(grid[r+1][cc] == 7 for cc in range(c+1,nxt+1))
            if blocked and mode != 'ignore_blocks':
                out[r+1][c] = 6
                events.append({'kind':'blocked_stop', 'row':r, 'col':c, 'run_end':end, 'next_col':nxt})
                break
            if roll_limit is not None and rolls >= roll_limit:
                out[r+1][c] = 6
                events.append({'kind':'shortcut_stop', 'row':r, 'col':c})
                break
            out[r][c], out[r+1][c] = 8, 4
            for cc in range(c+1,end+1):
                out[r+1][cc] = 2
            out[r+1][nxt] = 3
            events.append({'kind':'roll', 'row':r, 'col':c, 'run_end':end, 'next_col':nxt, 'length':end-c+1})
            rolls += 1
            if mode == 'reset_column':
                # Total wrong-intermediate rule: climb one row before reusing
                # the pre-roll column, rather than looping on the same ledge.
                r -= 1
            else:
                c = nxt
        else:
            out[0][c] = 6
            events.append({'kind':'top_exit', 'row':0, 'col':c})
        traces.append({'marker':[mr,mc], 'events':events})
    return out, traces


def trace(grid, direction, mode=None):
    _grid(grid)
    if direction not in DIRECTIONS or mode not in (None, *SHORTCUTS):
        raise ValueError('unsupported direction or shortcut')
    if direction == 'right':
        return _right(grid, mode)
    output, traces = _right([row[::-1] for row in grid], mode)
    width = len(grid[0])
    for t in traces:
        t['marker'][1] = width-1-t['marker'][1]
        for event in t['events']:
            for key in ('col', 'run_end', 'next_col'):
                if key in event:
                    event[key] = width-1-event[key]
    return [row[::-1] for row in output], traces


def predict(grid, direction, mode=None):
    return trace(grid, direction, mode)[0]


def _rng(seed, tag):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{tag}'.encode()).digest(), 'big'))


def _run(grid, row, first, last):
    if not (0 <= row < len(grid)-1 and 0 <= first <= last < len(grid[0])):
        raise ValueError('ladder exceeds the supported canvas')
    grid[row][first:last+1] = [7] * (last-first+1)


def _ladder(grid, center, rows, left, right):
    grid[-1][center] = 6
    lc = rc = center
    for index, row in enumerate(rows):
        _run(grid, row, lc-left[index]+1, lc)
        _run(grid, row, rc, rc+right[index]-1)
        lc -= left[index]
        rc += right[index]
    return lc, rc


def _block(grid, row, lc, rc):
    _run(grid, row, lc-1, lc)
    _run(grid, row, rc, rc+1)
    grid[row+1][lc-1] = grid[row+1][rc+1] = 7


def _decorate(grid, rng):
    """Add genuine off-path distractors without changing either route.

Every empty cell read along a successful route/check is painted in the output;
those cells and all structure cells are protected. Stops remain stops when more
orange is added. We also assert trace preservation rather than assume it.
"""
    before = {d: trace(grid,d) for d in DIRECTIONS}
    h, w = len(grid), len(grid[0])
    protected = {(r,c) for r in range(h) for c in range(w)
                 if grid[r][c] != 0 or any(before[d][0][r][c] != grid[r][c] for d in DIRECTIONS)}
    for direction in DIRECTIONS:
        for trace_row in before[direction][1]:
            for event in trace_row['events']:
                if 'next_col' in event:
                    row, start, end = event['row'], event['col'], event['next_col']
                    protected.add((row,end))
                    protected.update((row+1,c) for c in range(min(start,end),max(start,end)+1))
    candidates = [(r,c) for r in range(h-1) for c in range(w) if (r,c) not in protected]
    rng.shuffle(candidates)
    target = max(8, int(h*w*rng.uniform(.16,.23)))
    existing = sum(v == 7 for row in grid for v in row)
    for r,c in candidates[:max(0,target-existing)]:
        grid[r][c] = 7
    if any(trace(grid,d)[1] != before[d][1] for d in DIRECTIONS):
        raise AssertionError('off-path decoration changed a collision decision')
    return grid


def _scene(seed, tag, kind):
    rng = _rng(seed, tag)
    if kind == 'lesson_rolls':
        h,w = 28,30
        g = [[0]*w for _ in range(h)]
        left,right = [2,3,2,2,2,2],[3,2,2,2,3,2]
        rng.shuffle(left); rng.shuffle(right)
        _ladder(g,14,[23,19,15,11,7,3],left,right)
    elif kind == 'lesson_stops':
        h, w = rng.randint(20,26), rng.randint(26,30)
        g = [[0]*w for _ in range(h)]
        c1, c2 = 6+rng.randint(-1,1), w-7+rng.randint(-1,1)
        lc,rc = _ladder(g,c1,[h-5],[2],[2])
        _block(g,h-10,lc,rc)
        _ladder(g,c2,[h-5,h-10],[2,2],[2,2])
        _run(g,2,0,w-1)
    else:
        h,w = {'minimum':(14,14),'blocked':(20,24),'edge':(26,26),'stress':(30,30),'extra':(18,24)}[kind]
        g = [[0]*w for _ in range(h)]
        center = w//2-1
        if kind == 'stress':
            left, right = [2,3,2,2,2,2], [3,2,2,2,3,2]
            rng.shuffle(left); rng.shuffle(right)
            _ladder(g,center,[25,21,17,13,9,5],left,right)
        elif kind == 'minimum':
            _ladder(g,center,[9,5],[2,2],[2,2])
        elif kind == 'blocked':
            lc,rc = _ladder(g,center,[15,11],[3,2],[2,3])
            _block(g,6,lc,rc)
        elif kind == 'edge':
            _ladder(g,center,[21,17,13],[2,3,2],[3,2,2])
            _run(g,2,0,w-1)
        else:
            _ladder(g,center,[13,9,5],[rng.randint(1,3),2,1],[rng.randint(1,3),1,2])
    return _decorate(g,rng)


def teaching_check(train, settings):
    """Fit only visible demonstration labels; no query or private answer access."""
    chosen = _settings(settings)
    if type(train) is not list or not train:
        raise ValueError('a nonempty demonstration list is required')
    survivors = [d for d in DIRECTIONS if all(predict(p['input'],d) == p['output'] for p in train)]
    surviving = [m for m in SHORTCUTS if all(predict(p['input'],chosen,m) == p['output'] for p in train)]
    return {'survivors':survivors, 'surviving_shortcuts':surviving,
            'tested_shortcuts':list(SHORTCUTS), 'demonstration_only':True}


def generate(seed, settings, demos, queries):
    chosen = _settings(settings)
    for value,lo,hi,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,4,4,'queries')):
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{name} must be an integer in {lo}..{hi}')
    kinds = ['lesson_rolls','lesson_stops'] + ['extra']*(demos-2)
    inputs = [_scene(seed,f'demo:{i}',kind) for i,kind in enumerate(kinds)]
    tests = [_scene(seed,f'query:{i}',kind) for i,kind in enumerate(('minimum','blocked','edge','stress'))]
    all_inputs = inputs+tests
    if len({json.dumps(g) for g in all_inputs}) != len(all_inputs):
        raise ValueError('duplicate input draw; no shortened or cloned episode is returned')
    episode = {'train':[{'input':g,'output':predict(g,chosen)} for g in inputs],
               'test':[{'input':g,'output':predict(g,chosen)} for g in tests],
               'program_solution':program(settings), 'settings':dict(settings), 'seed':seed}
    report = teaching_check(episode['train'],settings)
    if report['survivors'] != [chosen] or report['surviving_shortcuts']:
        raise ValueError(f'demonstrations do not distinguish the declared rules: {report}')
    episode['teaching'] = report
    return episode


def public_turn(episode, query_index):
    """Project one query; expose no total count, future query or private field."""
    from reviewer_support import public_challenge_bytes
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('query index is out of range')
    visible = {'train':episode['train'], 'test':[episode['test'][query_index]]}
    return json.loads(public_challenge_bytes(visible))
