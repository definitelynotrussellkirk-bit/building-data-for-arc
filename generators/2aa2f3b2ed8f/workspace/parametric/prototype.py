"""Finite, proposed mover variants for the tailed-rectangle task.

Python labels are claims until the protected Racket worker executes them.
The input sampler is independent of the private episode setting and counts.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
TASK_ID = '2aa2f3b2ed8f'
SETTINGS = ({'mover': 'body'}, {'mover': 'target'})


def _load_geometry():
    path = HOME / 'generator.py'
    spec = importlib.util.spec_from_file_location('_tailed_rectangle_geometry_' + hashlib.sha256(str(path).encode()).hexdigest(), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GEOMETRY = _load_geometry()
# height, width, body height/width, target height/width, tail length.
# First two demonstrations reverse which role is larger, and turn 90 degrees.
_DEMOS = (
    (9, 14, 3, 4, 7, 5, 3),
    (10, 17, 6, 7, 2, 3, 4),
    (13, 18, 5, 6, 9, 7, 4),
    (12, 19, 8, 5, 4, 8, 5),
    (15, 22, 6, 8, 12, 7, 6),
    (14, 21, 9, 7, 5, 8, 5),
)
_QUERIES = (
    (2, 4, 2, 2, 1, 1, 1),
    (16, 22, 7, 8, 10, 8, 6),
    (24, 29, 12, 8, 20, 14, 7),
    (30, 30, 9, 11, 30, 11, 8),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {'mover'}
            or type(settings['mover']) is not str
            or settings['mover'] not in ('body', 'target')):
        raise ValueError("settings must be exactly {'mover': 'body'|'target'}")
    return settings['mover']


def program(settings):
    """Exact default authority or the separately named target-moving rule."""
    mover = _setting(settings)
    return (HERE / ('canonical.rkt' if mover == 'body' else 'target.rkt')).read_text()


def _rng(seed, split, index, attempt):
    raw = json.dumps([TASK_ID, seed, split, index, attempt], separators=(',', ':')).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), 'big'))


def _scene(rng, spec, rotation, color_order=None):
    height, width, bh, bw, th, tw, gap = spec
    colors = rng.sample(range(1, 10), 2)
    if color_order is not None:
        colors = sorted(colors, reverse=color_order)
    body_color, target_color = colors
    # Choose overlapping transverse spans constructively: the tail must hit
    # both objects, including at a corner; no shape/filter rejection loop.
    spans = [(b, t) for b in range(height - bh + 1)
             for t in range(height - th + 1)
             if max(b, t) <= min(b + bh - 1, t + th - 1)]
    body_top, target_top = rng.choice(spans)
    tail_row = rng.randint(max(body_top, target_top),
                          min(body_top + bh - 1, target_top + th - 1))
    left = rng.randint(0, width - (bw + gap + tw))
    target_left = left + bw + gap
    grid = [[0] * width for _ in range(height)]
    for row in range(body_top, body_top + bh):
        for col in range(left, left + bw):
            grid[row][col] = body_color
    for row in range(target_top, target_top + th):
        for col in range(target_left, target_left + tw):
            grid[row][col] = target_color
    for col in range(left + bw, target_left):
        grid[tail_row][col] = body_color
    for _ in range(rotation):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def sample_input(seed, index, *, split, attempt=0):
    """Deterministic prefix-stable inputs; no private setting enters this RNG."""
    _integer(seed, 0, 2**63 - 1, 'seed')
    _integer(attempt, 0, 31, 'attempt')
    if split not in ('train', 'test'):
        raise ValueError('split must be train or test')
    specs = _DEMOS if split == 'train' else _QUERIES
    _integer(index, 0, len(specs) - 1, 'index')
    rotation = (seed % 4 + index) % 4
    # Teach both color-rank orders within the first two demonstrations. This
    # defeats always-move-lower/higher-color without adding a demonstration;
    # seed parity varies which order comes first, independently of the mover.
    color_order = bool((seed + index) % 2) if split == 'train' and index < 2 else None
    return _scene(_rng(seed, split, index, attempt), specs[index], rotation, color_order)


def claimed_output(grid, settings):
    """Geometric Python claim, independently checked by the Racket worker."""
    mover = _setting(settings)
    geometry = _GEOMETRY._analyze_geometry(grid)
    steps = geometry['tail_length']
    dr, dc = geometry['vector']
    output = deepcopy(grid)
    if mover == 'body':
        erased = geometry['moving_cells']
        translated = geometry['body_cells']
        color = geometry['moving_color']
    else:
        erased = geometry['tail_cells'] | geometry['target_cells']
        translated = geometry['target_cells']
        color = geometry['target_color']
        dr, dc = -dr, -dc
    for row, col in erased:
        output[row][col] = 0
    for row, col in translated:
        nr, nc = row + dr * steps, col + dc * steps
        if not 0 <= nr < len(grid) or not 0 <= nc < len(grid[0]):
            raise ValueError('constructed translation would clip a selected object')
        if output[nr][nc] not in (0, color):
            raise ValueError('constructed translation would overlap the fixed object')
        output[nr][nc] = color
    return output


def generate(seed, settings, demos=3, queries=4):
    """Build a distinct episode; 2..6 demos and 1..4 queries independently.

    Every query prefix is identical at the same seed/settings/demos, enabling
    one-query evaluation and four-query sequential reveal with equal turn one.
    """
    _integer(seed, 0, 2**63 - 1, 'seed')
    _setting(settings)
    _integer(demos, 2, 6, 'demos')
    _integer(queries, 1, 4, 'queries')
    result = {'train': [], 'test': [], 'program_solution': program(settings)}
    seen = set()
    draws = 0
    for split, count in (('train', demos), ('test', queries)):
        for index in range(count):
            for attempt in range(32):
                grid = sample_input(seed, index, split=split, attempt=attempt)
                draws += 1
                key = json.dumps(grid, separators=(',', ':'))
                if key not in seen:
                    break
            else:
                raise ValueError(f'distinct input budget exhausted for {split}[{index}]')
            seen.add(key)
            result[split].append({'input': grid, 'output': claimed_output(grid, settings)})
    result['sampling'] = {'draws': draws, 'duplicate_rejections': draws - demos - queries}
    return result
