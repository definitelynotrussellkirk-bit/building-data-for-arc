"""Constructive, episode-fixed rolling direction with finite-rival teaching.

Python outputs are claims. Native qualification and exercise.py execute the
matching protected Racket programs before retaining labels as evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes

CANONICAL = Path(__file__).with_name('canonical.rkt').read_text()
DIRECTIONS = ('right', 'left')
RIVALS = ('opposite_direction', 'no_roll', 'stop_on_contact', 'cap_1', 'cap_2', 'cap_3',
          'ignore_blockers', 'adjacent_blocker_only', 'exclude_exit_blocker',
          'mutable_collision', 'reverse_markers', 'skip_roll_displacement')


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {'direction'}
            or type(settings['direction']) is not str
            or settings['direction'] not in DIRECTIONS):
        raise ValueError('settings must be exactly direction=right or direction=left')
    return settings['direction']


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def _directional(source, direction):
    if direction == 'right':
        return source
    if not source.startswith('(rule! ') or not source.endswith(')'):
        raise ValueError('expected one canonical rule! expression')
    body = source[len('(rule! '):-1]
    return '(rule! (lambda (g) (flip-lr (' + body + ' (flip-lr g)))))'


def program(settings):
    return _directional(CANONICAL, _setting(settings))


def _replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'canonical mutation anchor is not unique: {old}')
    return source.replace(old, new)


def rival_program(settings, name):
    direction = _setting(settings)
    if name not in RIVALS:
        raise ValueError('unknown declared rival')
    if name == 'opposite_direction':
        return program({'direction': 'left' if direction == 'right' else 'right'})
    source = CANONICAL
    if name == 'no_roll':
        source = _replace(source, '((= (at g r col) 7)', '((and #f (= (at g r col) 7))')
    elif name == 'stop_on_contact':
        source = _replace(source, '(if ok', '(if #f')
    elif name in ('cap_1', 'cap_2', 'cap_3'):
        cap = int(name[-1])
        source = _replace(source, '(col (second mag)))', '(col (second mag)) (rolls 0))')
        source = _replace(source, '(if ok', f'(if (and ok (< rolls {cap}))')
        source = _replace(source, '(trace r gc)', '(trace r gc (+ rolls 1))')
        source = _replace(source, '(trace (- r 1) col)', '(trace (- r 1) col rolls)')
    elif name == 'ignore_blockers':
        source = _replace(source, '(if ok', '(if #t')
    elif name == 'adjacent_blocker_only':
        source = _replace(source, '((> cc gc) (if ok', '((> cc (+ col 1)) (if ok')
    elif name == 'exclude_exit_blocker':
        source = _replace(source, '((> cc gc) (if ok', '((>= cc gc) (if ok')
    elif name == 'mutable_collision':
        for old, new in (
            ('(at g r col)', '(hash-ref result (list r col) 0)'),
            ('(at g r (+ re 1))', '(hash-ref result (list r (+ re 1)) 0)'),
            ('(at g (+ r 1) cc)', '(hash-ref result (list (+ r 1) cc) 0)'),
        ):
            source = _replace(source, old, new)
    elif name == 'reverse_markers':
        source = _replace(source, '(for ((mag magentas))', '(for ((mag (reverse magentas)))')
    elif name == 'skip_roll_displacement':
        source = _replace(source, '(trace r gc)', '(trace (- r 1) col)')
    return _directional(source, direction)


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or v not in (0, 6, 7) for v in row)
                   for row in grid)):
        raise ValueError('input must be an exact rectangular 1..30 grid of 0, 6 and 7')


def _right_trace(grid, mode=None):
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    markers = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 6]
    if mode == 'reverse_markers':
        markers.reverse()
    reads = set()

    def at(r, c):
        reads.add((r, c))
        return (output if mode == 'mutable_collision' else grid)[r][c]

    traces = []
    for mr, mc in markers:
        row, col, rolls = mr - 1, mc, 0
        events = []
        while True:
            if row < 0:
                output[0][col] = 6
                events.append({'kind': 'top_exit', 'row': 0, 'col': col})
                break
            if at(row, col) != 7 or mode == 'no_roll':
                output[row][col] = 2
                row -= 1
                continue
            end = col
            while end + 1 < width and at(row, end + 1) == 7:
                end += 1
            gap = end + 1
            if gap == width:
                output[row + 1][col] = 6
                events.append({'kind': 'edge_stop', 'row': row, 'col': col, 'run_end': end})
                break
            checked = range(col + 1, gap + 1)
            if mode == 'adjacent_blocker_only':
                checked = range(col + 1, col + 2)
            elif mode == 'exclude_exit_blocker':
                checked = range(col + 1, gap)
            # Evaluate the entire range, matching Racket's eager collision scan.
            obstacles = [at(row + 1, c) == 7 for c in checked]
            blocked = any(obstacles)
            if mode == 'ignore_blockers':
                blocked = False
            if mode == 'stop_on_contact' or (mode in ('cap_1', 'cap_2', 'cap_3') and rolls >= int(mode[-1])):
                blocked = True
            if blocked:
                output[row + 1][col] = 6
                events.append({'kind': 'blocked_stop', 'row': row, 'col': col,
                               'run_end': end, 'next_col': gap})
                break
            output[row][col], output[row + 1][col] = 8, 4
            for c in range(col + 1, end + 1):
                output[row + 1][c] = 2
            output[row + 1][gap] = 3
            events.append({'kind': 'roll', 'row': row, 'col': col, 'run_end': end,
                           'next_col': gap, 'length': end - col + 1})
            rolls += 1
            if mode == 'skip_roll_displacement':
                row -= 1
            else:
                col = gap
        traces.append({'marker': [mr, mc], 'events': events})
    return output, traces, reads


def trace(grid, settings, rival=None):
    _grid(grid)
    direction = _setting(settings)
    if rival is not None and rival not in RIVALS:
        raise ValueError('unknown declared rival')
    if rival == 'opposite_direction':
        direction = 'left' if direction == 'right' else 'right'
        rival = None
    if direction == 'right':
        return _right_trace(grid, rival)
    width = len(grid[0])
    output, traces, reads = _right_trace([row[::-1] for row in grid], rival)
    for item in traces:
        item['marker'][1] = width - 1 - item['marker'][1]
        for event in item['events']:
            for key in ('col', 'run_end', 'next_col'):
                if key in event:
                    event[key] = width - 1 - event[key]
    return [row[::-1] for row in output], traces, {(r, width - 1 - c) for r, c in reads}


def mirror(grid, settings, rival=None):
    return trace(grid, settings, rival)[0]


def _rng(seed, split, index):
    digest = hashlib.sha256(f'ba32-rolling-v1/{seed}/{split}/{index}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _run(grid, row, start, end):
    for col in range(start, end + 1):
        grid[row][col] = 7


def _cascade(rng, height, width, depth, marker_count=2):
    # Fit four real transitions even in the minimum 18x22 demonstration.
    # Wider queries retain variable 2/3-cell secondary ledges.
    step = min(3, (width - 9) // (2 * (depth - 1)))
    if step < 2:
        raise ValueError('canvas is too narrow for the requested cascade')
    reach = 4 + step * (depth - 1)
    center = rng.randint(reach, width - reach - 1)
    grid = [[0] * width for _ in range(height)]
    for col in ([center - 2, center + 2] if marker_count == 2 else [center - 2, center, center + 2]):
        grid[-1][col] = 6
    rows = [round(height - 4 - i * (height - 6) / (depth - 1)) for i in range(depth)]
    a, b = rng.randint(2, 3), rng.randint(2, 3)
    _run(grid, rows[0], center - a, center + b)
    left, right = center - a - 1, center + b + 1
    for row in rows[1:]:
        a, b = rng.randint(2, step), rng.randint(2, step)
        _run(grid, row, left - a + 1, left)
        _run(grid, row, right, right + b - 1)
        left -= a
        right += b
    return grid


def _stops(rng, height, width):
    grid = [[0] * width for _ in range(height)]
    center = width // 2 + rng.choice((-1, 0, 1))
    row = rng.randint(height // 2, height - 4)
    for col in (1, center, width - 2):
        grid[-1][col] = 6
    _run(grid, row, 0, 4)
    _run(grid, row, center - 2, center + 2)
    _run(grid, row, width - 5, width - 1)
    grid[row + 1][center - 3] = grid[row + 1][center + 3] = 7
    return grid


def _noise(grid, rng, density):
    protected = set()
    for direction in DIRECTIONS:
        protected |= trace(grid, {'direction': direction})[2]
    height, width = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(height - 1) for c in range(width)
                  if grid[r][c] == 0 and (r, c) not in protected]
    rng.shuffle(candidates)
    target = int(height * width * density)
    existing = sum(v == 7 for row in grid for v in row)
    for r, c in candidates[:max(0, target - existing)]:
        grid[r][c] = 7
    for r, c in ((0, 0), (0, width - 1), (height - 2, 0), (height - 2, width - 1)):
        if (r, c) not in protected:
            grid[r][c] = 7
    return grid


def _scene(seed, split, index):
    rng = _rng(seed, split, index)
    if split == 'train' and index == 0:
        grid = _cascade(rng, 18, 22, 4)
    elif split == 'train' and index == 1:
        grid = _stops(rng, 22, 26)
    elif split == 'test' and index == 0:
        grid = _cascade(rng, 26, 30, 4)
    elif split == 'test' and index == 1:
        grid = _stops(rng, 24, 28)
    elif split == 'test' and index == 2:
        grid = _cascade(rng, 23, 26, 2, marker_count=3)
    elif split == 'test' and index == 3:
        grid = _cascade(rng, 30, 30, 4, marker_count=3)
    else:
        height, width = rng.randint(18, 30), rng.randint(22, 30)
        grid = (_cascade(rng, height, width, 3, marker_count=3)
                if index % 2 == 0 else _stops(rng, height, width))
    return _noise(grid, rng, 0.22 if split == 'test' and index == 3 else rng.uniform(0.10, 0.18))


def teaching_check(episode, settings):
    """Finite mirror guard; exercise.py supplies independent Racket evidence."""
    results = []
    for rival in RIVALS:
        refuting = [i for i, p in enumerate(episode['train'])
                    if mirror(p['input'], settings, rival) != p['output']]
        disagreements = [i for i, p in enumerate(episode['test'])
                         if mirror(p['input'], settings, rival) != p['output']]
        if not refuting and disagreements:
            raise ValueError(f'underidentified lesson: {rival}, queries {disagreements}')
        results.append({'rival': rival, 'refuting_demos': refuting,
                        'query_disagreements': disagreements})
    return results


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, 'seed')
    _integer(demos, 2, 6, 'demos')
    _integer(queries, 1, 4, 'queries')
    _setting(settings)
    result = {'program_solution': program(settings), 'settings': dict(settings), 'seed': seed}
    for split, count in (('train', demos), ('test', queries)):
        result[split] = []
        for index in range(count):
            grid = _scene(seed, split, index)
            result[split].append({'input': grid, 'output': mirror(grid, settings)})
    keys = [json.dumps(pair['input']) for split in ('train', 'test') for pair in result[split]]
    if len(set(keys)) != len(keys):
        raise ValueError('constructive sampler generated duplicate inputs')
    result['teaching'] = teaching_check(result, settings)
    return result


def public_query_bytes(episode, index=0):
    _integer(index, 0, len(episode['test']) - 1, 'query index')
    return public_challenge_bytes({'train': episode['train'], 'test': [episode['test'][index]]})
