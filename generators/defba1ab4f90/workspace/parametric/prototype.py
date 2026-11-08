"""Paired, guarded stream scenes with an episode-fixed handedness rule.

Python outputs are claims. Native qualification independently executes the exact
Racket programs. Both settings use the SAME inputs; no setting is encoded in the
sampler seed, geometry, orientation, colors or query order.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

TASK_ID = 'defba1ab4f90'
MODES = ('canonical', 'reversed')
RIVALS = ('always_blue', 'always_green', 'no_chirality_flip', 'row_first_bar')
CANONICAL = Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
_STEP = '(if (= (at gg (+ r 1) c) 1) blue-step (- blue-step))'
_DEMOS = ((14, 14, 5, 'top'), (17, 17, 6, 'left'), (19, 21, 7, 'top'),
          (22, 20, 8, 'left'), (25, 25, 10, 'top'), (28, 28, 11, 'left'))
_QUERIES = ((22, 24, 8, 'top'), (25, 27, 10, 'left'),
            (30, 30, 12, 'top'), (30, 30, 12, 'left'))


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {'handedness'}:
        raise ValueError('settings must contain exactly handedness')
    mode = settings['handedness']
    if type(mode) is not str or mode not in MODES:
        raise ValueError('handedness must be canonical or reversed')
    return mode


def _replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f'Pinned canonical source no longer has one {before!r}')
    return text.replace(before, after)


def program(settings):
    """Default bytes are canonical, not a regenerated equivalent program."""
    mode = _settings(settings)
    if mode == 'canonical':
        return CANONICAL
    source = _replace_once(CANONICAL, '(flow (transpose g) -1)', '(flow (transpose g) 1)')
    return _replace_once(source, '(flow g 1)', '(flow g -1)')


def rival_program(settings, rival):
    """Plausible, total-on-our-grammar counterprograms for bounded teaching checks."""
    mode = _settings(settings)
    if rival not in RIVALS:
        raise ValueError('unknown rival')
    source = program(settings)
    if rival == 'always_blue':
        return _replace_once(source, _STEP, 'blue-step')
    if rival == 'always_green':
        return _replace_once(source, _STEP, '(- blue-step)')
    if rival == 'no_chirality_flip':
        left, top = (-1, 1) if mode == 'canonical' else (1, -1)
        return _replace_once(source, f'(flow (transpose g) {left})', f'(flow (transpose g) {top})')
    return _replace_once(source, '(at gg (+ r 1) c)',
                         '(first (filter (lambda (v) (not (zero? v))) (list-ref gg (+ r 1))))')


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _normalize(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid height must be 1..30')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid width must be 1..30')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(x) is not int or x not in (0, 1, 2, 3) for row in grid for x in row):
        raise ValueError('grid cells must be exact integers in the task palette')
    markers = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == 2]
    if len(markers) != 1:
        raise ValueError('exactly one red entry marker is required')
    r, c = markers[0]
    if r == 0 and 0 < c < width - 1:
        return deepcopy(grid), False
    if c == 0 and 0 < r < len(grid) - 1:
        return _transpose(grid), True
    raise ValueError('entry marker must be on the top or left edge, not a corner')


def trace(grid, settings, *, rival=None):
    """Independent bounded Python claim; events use normalized top-entry coordinates."""
    mode = _settings(settings)
    if rival is not None and rival not in RIVALS:
        raise ValueError('unknown rival')
    latent, transposed = _normalize(grid)
    h, w = len(latent), len(latent[0])
    blue = (-1 if transposed else 1) * (-1 if mode == 'reversed' else 1)
    if rival == 'no_chirality_flip':
        blue = -1 if mode == 'reversed' else 1
    c = latent[0].index(2); r = 0
    out = deepcopy(latent); events = []
    while r < h - 1:
        if latent[r + 1][c] == 0:
            r += 1; out[r][c] = 2
            continue
        color = latent[r + 1][c]
        selected = color
        if rival == 'always_blue':
            selected = 1
        elif rival == 'always_green':
            selected = 3
        elif rival == 'row_first_bar':
            selected = next(x for x in latent[r + 1] if x != 0)
        step = blue if selected == 1 else -blue
        before = c
        for _ in range(w):
            c += step
            if not 0 <= c < w:
                raise ValueError('stream exits the lane; input is outside the guarded grammar')
            out[r][c] = 2
            if latent[r + 1][c] == 0:
                r += 1; out[r][c] = 2
                events.append({'row': r, 'column': before, 'color': color,
                               'selected_color': selected, 'exit_column': c})
                break
        else:
            raise ValueError('bounded slide failed to find a gap')
    return (_transpose(out) if transposed else out), events


def _rng(seed, label):
    digest = hashlib.sha256(f'{TASK_ID}:paired-stream-v1:{seed}:{label}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


@lru_cache(maxsize=8192)
def _transitions(width, c0, c1, blue, final):
    """One or two separated bars covering both current path columns."""
    choices = []
    for c, sense in ((c0, blue), (c1, -blue)):
        options = []
        for start in range(max(1, c - 2), min(c, width - 4) + 1):
            for color in (1, 3):
                direction = sense if color == 1 else -sense
                nxt = start + 3 if direction > 0 else start - 1
                if final or 1 <= nxt <= width - 2:
                    options.append((start, color, nxt))
        choices.append(options)
    found = set()
    for s0, color0, next0 in choices[0]:
        for s1, color1, next1 in choices[1]:
            if s0 == s1 and color0 == color1:
                bars = ((s0, color0),)
            elif abs(s0 - s1) >= 4:
                bars = tuple(sorted(((s0, color0), (s1, color1))))
            else:
                continue
            found.add((bars, (next0, next1), (color0, color1)))
    return tuple(sorted(found))


def _route_plan(rng, width, layers, blue):
    """Bounded constructive search; both rules hit every layer and both colors."""
    start = rng.choice(range(width // 2 - 1, width // 2 + 2))
    failed = set(); nodes = 0

    def walk(depth, columns, masks, last, repeats):
        nonlocal nodes
        nodes += 1
        if nodes > 50000:
            raise RuntimeError('paired-route construction exhausted its 50000-node budget')
        if depth == layers:
            return [] if masks == (3, 3) and repeats == 3 else None
        state = (depth, columns, masks, last, repeats)
        if state in failed:
            return None
        options = list(_transitions(width, *columns, blue, depth == layers - 1))
        target = (width - 4, 3) if depth < layers // 2 else (3, width - 4)
        ranked = sorted(options, key=lambda item: (
            abs(item[1][0] - target[0]) + abs(item[1][1] - target[1]) + rng.random() * 5))
        for bars, nxt, colors in ranked:
            next_masks = tuple(masks[i] | (1 if colors[i] == 1 else 2) for i in range(2))
            next_repeats = repeats | sum((1 << i) for i in range(2) if colors[i] == last[i])
            suffix = walk(depth + 1, nxt, next_masks, colors, next_repeats)
            if suffix is not None:
                return [(bars, nxt, colors)] + suffix
        failed.add(state)
        return None

    route = walk(0, (start, start), (0, 0), (0, 0), 0)
    if route is None:
        raise RuntimeError('no paired route exists for the requested geometry')
    return start, route


def _sample(seed, label, profile):
    height, width, layers, orientation = profile
    rng = _rng(seed, label)
    blue = 1 if orientation == 'top' else -1
    marker, plan = _route_plan(rng, width, layers, blue)
    rows = [2 + i * (height - 4) // (layers - 1) for i in range(layers)]
    grid = [[0] * width for _ in range(height)]
    grid[0][marker] = 2
    for row, (active, _, _) in zip(rows, plan):
        bars = list(active)
        # Fill the unused lanes with inert, separated bars. Blank one-cell gaps
        # preserve both constructed exits, including exits beside distractors.
        starts = list(range(1, width - 3)); rng.shuffle(starts)
        starts = [1, width - 4] + starts
        for start in starts:
            if all(abs(start - existing) >= 4 for existing, _ in bars):
                bars.append((start, rng.choice((1, 3))))
        for start, color in bars:
            grid[row][start:start + 3] = [color] * 3
    result = _transpose(grid) if orientation == 'left' else grid
    for mode in MODES:
        _, events = trace(result, {'handedness': mode})
        if len(events) != layers or {e['color'] for e in events} != {1, 3}:
            raise RuntimeError('constructed input violated its two-route contract')
    return result


def teaching_certificate(train, settings):
    """Fit demonstrations only; this function never takes or examines queries."""
    mode = _settings(settings)
    if type(train) is not list or not train:
        raise ValueError('nonempty demonstrations are required')
    for pair in train:
        if trace(pair['input'], settings)[0] != pair['output']:
            raise ValueError('demonstration claim disagrees with the chosen rule')
    survivors = [dict(handedness=candidate) for candidate in MODES
                 if all(trace(p['input'], {'handedness': candidate})[0] == p['output'] for p in train)]
    rivals = [rival for rival in RIVALS
              if all(trace(p['input'], settings, rival=rival)[0] == p['output'] for p in train)]
    if survivors != [{'handedness': mode}] or rivals:
        raise ValueError(f'underidentified demonstration set: {survivors!r}, rivals={rivals!r}')
    return {'surviving_settings': survivors, 'surviving_rivals': rivals,
            'tested_rivals': list(RIVALS), 'scope': 'finite demonstration-only Python certificate; native Racket required'}


def generate(seed, settings, demos, queries):
    """Native contract, independent counts, query-prefix stability, matched inputs."""
    _integer(seed, 0, 2**63 - 1, 'seed'); _settings(settings)
    _integer(demos, 2, 6, 'demos'); _integer(queries, 1, 4, 'queries')
    # Selection is deliberately checked under BOTH settings so a retry cannot
    # encode the private setting in the visible input distribution.
    for attempt in range(16):
        demo_inputs = [_sample(seed, f'demo:{attempt}:{i}', _DEMOS[i]) for i in range(demos)]
        try:
            for mode in MODES:
                chosen = {'handedness': mode}
                teaching_certificate([{'input': g, 'output': trace(g, chosen)[0]} for g in demo_inputs], chosen)
        except ValueError:
            continue
        break
    else:
        raise RuntimeError('no distinguishing demonstration set within 16 paired attempts')
    query_inputs = [_sample(seed, f'query:{i}', _QUERIES[i]) for i in range(queries)]
    inputs = demo_inputs + query_inputs
    if len({json.dumps(g) for g in inputs}) != len(inputs):
        raise RuntimeError('duplicate visible input; no shortened batch is emitted')
    pairs = [{'input': g, 'output': trace(g, settings)[0]} for g in inputs]
    return {'train': pairs[:demos], 'test': pairs[demos:], 'program_solution': program(settings),
            'private': {'settings': deepcopy(settings), 'input_seed': seed, 'demo_attempts': attempt + 1,
                        'teaching': teaching_certificate(pairs[:demos], settings)}}


def public_turn(episode, query_index):
    """One actor-facing turn, with no future query, count, private rule or label."""
    _integer(query_index, 0, len(episode['test']) - 1, 'query_index')
    return {'train': [{'input': deepcopy(p['input']), 'output': deepcopy(p['output'])}
                      for p in episode['train']],
            'test': [{'input': deepcopy(episode['test'][query_index]['input'])}]}
