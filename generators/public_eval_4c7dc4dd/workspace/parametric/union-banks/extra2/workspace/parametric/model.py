"""Constructive transfer-panel family for public parent 4c7dc4dd.

Four congruent square panels are arranged as two examples inside two large
monochrome frames.  One pair demonstrates an input-dependent transformation;
the other pair contains a query and an empty slot.  The canonical answer is the
transformed query interior.  The alternate answer is a causal change mask made
only after the transformed intermediate exists.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from pathlib import Path
import hashlib
import json
import random

HERE = Path(__file__).resolve().parent
SETTINGS = ('transformed', 'change_mask')
OPERATIONS = ('connect', 'complement', 'corner_expand')


def strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('expected a rectangular 1..30 grid of exact integer colors 0..9')
    return [row[:] for row in grid]


def _bbox_overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _uniform_square_frames(grid):
    h, w = len(grid), len(grid[0]); by_side = {}
    for side in range(4, min(10, h, w) + 1):
        found = []
        for r in range(h - side + 1):
            for c in range(w - side + 1):
                color = grid[r][c]
                if color == 0:
                    continue
                if (all(grid[r][x] == color and grid[r + side - 1][x] == color
                        for x in range(c, c + side))
                        and all(grid[x][c] == color and grid[x][c + side - 1] == color
                                for x in range(r, r + side))):
                    found.append({'r': r, 'c': c, 'side': side, 'color': color,
                                  'bbox': (r, c, r + side - 1, c + side - 1)})
        if len(found) >= 4:
            by_side[side] = found
    if not by_side:
        raise ValueError('expected four congruent square panel frames')
    side = max(by_side)
    candidates = by_side[side]
    disjoint = [combo for combo in combinations(candidates, 4)
                if all(not _bbox_overlap(a['bbox'], b['bbox']) for a, b in combinations(combo, 2))]
    if len(disjoint) != 1:
        raise ValueError('expected one set of four disjoint largest panel frames')
    frames = list(disjoint[0])
    for frame in frames:
        r, c, s = frame['r'], frame['c'], frame['side']
        frame['grid'] = [row[c + 1:c + s - 1] for row in grid[r + 1:r + s - 1]]
    return frames


def _prefixes(grid):
    h, w = len(grid), len(grid[0])
    rows = [[[0] * (w + 1) for _ in range(h)] for _ in range(10)]
    cols = [[[0] * (h + 1) for _ in range(w)] for _ in range(10)]
    for color in range(10):
        for r in range(h):
            for c in range(w):
                rows[color][r][c + 1] = rows[color][r][c] + (grid[r][c] == color)
        for c in range(w):
            for r in range(h):
                cols[color][c][r + 1] = cols[color][c][r] + (grid[r][c] == color)
    return rows, cols


def _rect_border_color(grid, prefixes, r0, c0, r1, c1):
    color = grid[r0][c0]
    if color == 0 or grid[r0][c1] != color or grid[r1][c0] != color or grid[r1][c1] != color:
        return None
    rows, cols = prefixes; width = c1 - c0 + 1; height = r1 - r0 + 1
    if (rows[color][r0][c1 + 1] - rows[color][r0][c0] == width
            and rows[color][r1][c1 + 1] - rows[color][r1][c0] == width
            and cols[color][c0][r1 + 1] - cols[color][c0][r0] == height
            and cols[color][c1][r1 + 1] - cols[color][c1][r0] == height):
        return color
    return None


def _enclosing_frame(grid, prefixes, frames, i, j):
    h, w = len(grid), len(grid[0]); a, b = frames[i], frames[j]
    top = min(a['bbox'][0], b['bbox'][0]); bottom = max(a['bbox'][2], b['bbox'][2])
    left = min(a['bbox'][1], b['bbox'][1]); right = max(a['bbox'][3], b['bbox'][3])
    best = None
    for r0 in range(top):
        for r1 in range(bottom + 1, h):
            for c0 in range(left):
                for c1 in range(right + 1, w):
                    color = _rect_border_color(grid, prefixes, r0, c0, r1, c1)
                    if color is None:
                        continue
                    inside = {k for k, f in enumerate(frames)
                              if r0 < f['bbox'][0] and c0 < f['bbox'][1]
                              and f['bbox'][2] < r1 and f['bbox'][3] < c1}
                    if inside != {i, j}:
                        continue
                    row = ((r1 - r0 + 1) * (c1 - c0 + 1), r0, c0, r1, c1, color)
                    if best is None or row < best:
                        best = row
    if best is None:
        return None
    _, r0, c0, r1, c1, color = best
    return {'indices': (i, j), 'bbox': (r0, c0, r1, c1), 'color': color}


def _groups(grid, frames):
    prefixes = _prefixes(grid); candidates = {}
    for i, j in combinations(range(4), 2):
        found = _enclosing_frame(grid, prefixes, frames, i, j)
        if found is not None:
            candidates[(i, j)] = found
    pairings = (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)))
    valid = []
    for first, second in pairings:
        if first in candidates and second in candidates:
            a, b = candidates[first], candidates[second]
            score = ((a['bbox'][2] - a['bbox'][0] + 1) * (a['bbox'][3] - a['bbox'][1] + 1)
                     + (b['bbox'][2] - b['bbox'][0] + 1) * (b['bbox'][3] - b['bbox'][1] + 1))
            valid.append((score, first, second, a, b))
    if not valid:
        raise ValueError('expected two large frames pairing the four panels')
    valid.sort(key=lambda row: row[:3])
    return [valid[0][3], valid[0][4]]


def _count_nonzero(grid):
    return sum(v != 0 for row in grid for v in row)


def _parity_colors(panel, fallback):
    maps = []
    for parity in (0, 1):
        counts = Counter(panel[r][c] for r in range(len(panel)) for c in range(len(panel[0]))
                         if panel[r][c] != 0 and (r + c) % 2 == parity)
        if not counts:
            maps.append(fallback)
        else:
            best = max(counts.values())
            winners = [color for color, count in counts.items() if count == best]
            maps.append(fallback if fallback in winners else min(winners))
    return maps


def _complement(panel, role_color):
    colors = _parity_colors(panel, role_color)
    return [[0 if panel[r][c] != 0 else colors[(r + c) % 2]
             for c in range(len(panel[0]))] for r in range(len(panel))]


def _connect(panel, role_color):
    out = [row[:] for row in panel]; h, w = len(panel), len(panel[0])
    marks = {(r, c) for r in range(h) for c in range(w) if panel[r][c] != 0}
    for r in range(h):
        cols = [c for rr, c in marks if rr == r]
        if len(cols) >= 2:
            for c in range(min(cols), max(cols) + 1):
                if out[r][c] == 0:
                    out[r][c] = role_color
    for c in range(w):
        rows = [r for r, cc in marks if cc == c]
        if len(rows) >= 2:
            for r in range(min(rows), max(rows) + 1):
                if out[r][c] == 0:
                    out[r][c] = role_color
    return out


def _corner_seed(panel):
    h, w = len(panel), len(panel[0])
    if h < 4 or w < 4:
        raise ValueError('corner expansion requires at least a 4x4 panel')
    nonzero = {(r, c) for r in range(h) for c in range(w) if panel[r][c] != 0}
    matches = []
    for bottom in (False, True):
        for right in (False, True):
            region = {(h - 1 - dr if bottom else dr, w - 1 - dc if right else dc)
                      for dr in range(2) for dc in range(2)}
            if nonzero <= region and len(nonzero) == 3:
                seed = [[panel[h - 1 - dr if bottom else dr][w - 1 - dc if right else dc]
                         for dc in range(2)] for dr in range(2)]
                if seed[0][0] == 0 and seed[0][1] == seed[1][0] != 0 and seed[1][1] != 0:
                    matches.append(seed)
    if len(matches) != 1:
        raise ValueError('expected one three-cell corner seed')
    return matches[0]


def _corner_expand(panel):
    seed = _corner_seed(panel); h, w = len(panel), len(panel[0])
    out = []
    for r in range(h):
        row = []
        for c in range(w):
            dr = min(r, h - 1 - r); dc = min(c, w - 1 - c)
            row.append(seed[dr][dc] if dr < 2 and dc < 2 else seed[1][1])
        out.append(row)
    return out


def _infer_operation(first, second, role_color):
    candidates = []
    if _complement(first, role_color) == second or _complement(second, role_color) == first:
        candidates.append('complement')
    sparse, dense = sorted((first, second), key=_count_nonzero)
    if _connect(sparse, role_color) == dense and sparse != dense:
        candidates.append('connect')
    try:
        expanded = _corner_expand(sparse)
    except ValueError:
        expanded = None
    if expanded == dense and sparse != dense:
        candidates.append('corner_expand')
    if len(candidates) != 1:
        raise ValueError('demonstration pair must identify exactly one operation')
    return candidates[0]


def analyze(grid):
    grid = strict_grid(grid); frames = _uniform_square_frames(grid); groups = _groups(grid, frames)
    empties = [i for i, frame in enumerate(frames)
               if all(v == 0 for row in frame['grid'] for v in row)]
    if len(empties) != 1:
        raise ValueError('expected exactly one empty output slot')
    empty = empties[0]
    query_groups = [group for group in groups if empty in group['indices']]
    if len(query_groups) != 1:
        raise ValueError('empty slot must belong to exactly one large frame')
    query_group = query_groups[0]
    query_index = next(i for i in query_group['indices'] if i != empty)
    demo_group = next(group for group in groups if group is not query_group)
    a, b = (frames[i]['grid'] for i in demo_group['indices'])
    operation = _infer_operation(a, b, demo_group['color'])
    query = frames[query_index]['grid']
    return {
        'panels': frames, 'groups': groups, 'operation': operation,
        'query': query, 'query_index': query_index, 'query_color': query_group['color'],
        'slot_index': empty, 'slot_color': frames[empty]['color'],
        'demo_color': demo_group['color'],
    }


def _transformed(info):
    if info['operation'] == 'complement':
        return _complement(info['query'], info['query_color'])
    if info['operation'] == 'connect':
        return _connect(info['query'], info['query_color'])
    if info['operation'] == 'corner_expand':
        return _corner_expand(info['query'])
    raise ValueError('unknown operation')


def solve(grid, result_view='transformed'):
    if result_view not in SETTINGS:
        raise ValueError('unknown result view')
    info = analyze(grid); full = _transformed(info)
    if result_view == 'transformed':
        return full
    return [[info['slot_color'] if full[r][c] != info['query'][r][c] else 0
             for c in range(len(full[0]))] for r in range(len(full))]


def program(settings):
    if (type(settings) is not dict or set(settings) != {'result_view'}
            or settings['result_view'] not in SETTINGS):
        raise ValueError('settings must name exactly one declared result_view')
    source = (HERE / 'canonical.rkt').read_text(encoding='utf-8')
    if settings['result_view'] == 'transformed':
        return source
    marker = '(define result-view "transformed")'
    if source.count(marker) != 1:
        raise ValueError('canonical result-view marker missing or duplicated')
    return source.replace(marker, '(define result-view "change_mask")', 1)


def _rng(seed, domain):
    token = hashlib.sha256(f'transfer-panel-v1:{seed}:{domain}'.encode()).digest()
    return random.Random(int.from_bytes(token, 'big'))


def _turn(grid, rotation=0, reflection=False):
    out = [row[::-1] if reflection else row[:] for row in grid]
    for _ in range(rotation % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _draw_border(grid, box, color):
    r0, c0, r1, c1 = box
    for c in range(c0, c1 + 1):
        grid[r0][c] = grid[r1][c] = color
    for r in range(r0, r1 + 1):
        grid[r][c0] = grid[r][c1] = color


def _draw_panel(grid, top, left, side, frame_color, interior):
    _draw_border(grid, (top, left, top + side - 1, left + side - 1), frame_color)
    for r, row in enumerate(interior):
        for c, value in enumerate(row):
            grid[top + 1 + r][left + 1 + c] = value


def _complement_source(n, role, accent, rng):
    out = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if rng.randrange(100) < 38:
                out[r][c] = role if (r + c) % 2 == 0 else accent
    out[0][0] = role; out[0][1] = accent; out[n - 1][n - 1] = role
    out[1][1] = 0
    return out


def _marker_source(n, role, accent, rng):
    r = 1 + rng.randrange(max(1, n - 2)); c = 1 + rng.randrange(max(1, n - 2))
    rr = 0 if r >= n // 2 else n - 1; cc = 0 if c >= n // 2 else n - 1
    out = [[0] * n for _ in range(n)]
    out[r][c] = accent; out[r][cc] = role; out[rr][c] = role
    return out


def _corner_source(n, role, accent, corner):
    bottom, right = corner; out = [[0] * n for _ in range(n)]
    seed = ((0, accent), (accent, role))
    for dr in range(2):
        for dc in range(2):
            r = n - 1 - dr if bottom else dr; c = n - 1 - dc if right else dc
            out[r][c] = seed[dr][dc]
    return out


def _layout(side, vertical):
    if not vertical:
        return [
            {'outer': (1, 1, 13, 28), 'panels': ((3, 3), (4, 28 - side - 1))},
            {'outer': (16, 2, 28, 27), 'panels': ((18, 4), (17, 27 - side - 1))},
        ]
    return [
        {'outer': (1, 1, 28, 13), 'panels': ((3, 3), (28 - side - 1, 4))},
        {'outer': (2, 16, 27, 28), 'panels': ((4, 18), (27 - side - 1, 19))},
    ]


def scene(seed, domain, operation, stress=False):
    if operation not in OPERATIONS:
        raise ValueError('unknown operation')
    rng = _rng(seed, domain); side = 8 if stress else rng.choice((6, 7, 8)); n = side - 2
    colors = list(range(1, 10)); rng.shuffle(colors)
    demo_role, query_role, demo_frame, query_frame, demo_accent, query_accent = colors[:6]
    noise = [0, *colors[6:]]
    grid = [[noise[(r * 7 + c * 3 + (r % 3) * (c % 2) + 1) % len(noise)]
             for c in range(30)] for r in range(30)]
    layouts = _layout(side, vertical=bool(rng.randrange(2)))
    if rng.randrange(2):
        layouts.reverse()
    demo_layout, query_layout = layouts
    _draw_border(grid, demo_layout['outer'], demo_role)
    _draw_border(grid, query_layout['outer'], query_role)
    if operation == 'complement':
        demo_a = _complement_source(n, demo_role, demo_accent, rng)
        demo_b = _complement(demo_a, demo_role)
        query = _complement_source(n, query_role, query_accent, rng)
    elif operation == 'connect':
        demo_a = _marker_source(n, demo_role, demo_accent, rng)
        demo_b = _connect(demo_a, demo_role)
        query = _marker_source(n, query_role, query_accent, rng)
    else:
        demo_a = _corner_source(n, demo_role, demo_accent, (bool(rng.randrange(2)), bool(rng.randrange(2))))
        demo_b = _corner_expand(demo_a)
        query = _corner_source(n, query_role, query_accent, (bool(rng.randrange(2)), bool(rng.randrange(2))))
    if rng.randrange(2):
        demo_a, demo_b = demo_b, demo_a
    dp = list(demo_layout['panels']); qp = list(query_layout['panels'])
    if rng.randrange(2):
        qp.reverse()
    _draw_panel(grid, *dp[0], side, demo_frame, demo_a)
    _draw_panel(grid, *dp[1], side, demo_frame, demo_b)
    _draw_panel(grid, *qp[0], side, query_frame, query)
    _draw_panel(grid, *qp[1], side, query_frame, [[0] * n for _ in range(n)])
    return _turn(grid, rng.randrange(4), bool(rng.randrange(2)))


def generate(seed, settings, demos, queries):
    if type(seed) is not int or isinstance(seed, bool) or not 0 <= seed < 2**63:
        raise ValueError('seed must be a nonnegative 63-bit integer')
    if (type(settings) is not dict or set(settings) != {'result_view'}
            or settings['result_view'] not in SETTINGS):
        raise ValueError('settings must name exactly one declared result_view')
    if type(demos) is not int or isinstance(demos, bool) or not 2 <= demos <= 6:
        raise ValueError('demos must be 2..6')
    if type(queries) is not int or isinstance(queries, bool) or queries != 4:
        raise ValueError('exactly four private queries are required')
    train = [scene(seed, f'demo:{i}', OPERATIONS[i % len(OPERATIONS)], stress=(i == 5))
             for i in range(demos)]
    bank = [scene(seed, f'query:{i}', OPERATIONS[(i + 1) % len(OPERATIONS)], stress=(i == 3))
            for i in range(4)]
    _rng(seed, 'presentation').shuffle(bank)
    label = lambda g: {'input': g, 'output': solve(g, settings['result_view'])}
    return {'train': [label(g) for g in train], 'test': [label(g) for g in bank],
            'program_solution': program(settings)}


def surviving_settings(episode):
    return [setting for setting in SETTINGS
            if all(solve(pair['input'], setting) == pair['output'] for pair in episode['train'])]


def rival(grid, result_view, name):
    info = analyze(grid)
    if name == 'opposite_setting':
        return solve(grid, SETTINGS[1 - SETTINGS.index(result_view)])
    if name == 'identity':
        return [row[:] for row in info['query']]
    if name == 'always_complement':
        full = _complement(info['query'], info['query_color'])
    elif name == 'always_connect':
        full = _connect(info['query'], info['query_color'])
    else:
        raise ValueError('unknown rival')
    if result_view == 'transformed':
        return full
    return [[info['slot_color'] if full[r][c] != info['query'][r][c] else 0
             for c in range(len(full[0]))] for r in range(len(full))]


def public_view(episode, query_index=0):
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('invalid query index')
    visible = {
        'train': [{'input': strict_grid(p['input']), 'output': strict_grid(p['output'])}
                  for p in episode['train']],
        'test': [{'input': strict_grid(episode['test'][query_index]['input'])}],
    }
    return (json.dumps(visible, sort_keys=True, separators=(',', ':')) + '\n').encode()


def dependency():
    return {
        'step_a': 'Infer the demonstrated operation and apply it to the query panel, producing the complete transformed panel.',
        'intermediate': 'The transformed query grid before any comparison with the original query.',
        'step_b': 'Compare that transformed intermediate cellwise with the query and paint changed cells with the empty slot frame color.',
        'why_b_depends_on_a': 'The mask has no changed-cell locations until the input-dependent operation has produced the transformed query.',
    }
