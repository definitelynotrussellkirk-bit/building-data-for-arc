"""Counted canvas dimensions, resized background, and transparent foreground tile.

Fresh nonuniform backgrounds use integer stretch factors, avoiding an ambiguity
the original examples do not resolve. The general solver defines floor-index
nearest-neighbor resampling for other lawful original shapes.
"""
from __future__ import annotations
import hashlib
import random

GENERATOR_ID = 'public_eval_f931b4a8'
TASK_ID = GENERATOR_ID
RULE_TASK_ID = 'ee_f931b4a8'
VERSION = '1.0.0'
SUMMARY = 'Count output dimensions, stretch the lower-left background, and tile the nonzero lower-right foreground.'
EXAMPLES_NEEDED = 2
INVARIANTS = ['four square quadrants', 'positive nonzero-cell counts at most 30 in the upper quadrants',
              'zero in the lower-right tile means transparency']
AXES = {'quadrant_side': {'type': 'int', 'valid': '2..15', 'default': '2..15'},
        'output_h': {'type': 'int', 'valid': 'positive multiple of quadrant_side, <=min(30,side^2)', 'default': 'sampled'},
        'output_w': {'type': 'int', 'valid': 'positive multiple of quadrant_side, <=min(30,side^2)', 'default': 'sampled'}}
MODES = ('stretch', 'repeat')


def integer(value, name, low=0, high=2**63 - 1):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def analyze(g):
    if (type(g) is not list or not 4 <= len(g) <= 30 or len(g) % 2
            or any(type(row) is not list or len(row) != len(g)
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('Expected an even square exact-integer color grid, side 4..30')
    side = len(g) // 2
    height = sum(g[r][c] != 0 for r in range(side) for c in range(side))
    width = sum(g[r][c] != 0 for r in range(side) for c in range(side, 2 * side))
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError('Upper quadrants must specify positive dimensions at most 30')
    return {'side': side, 'output_h': height, 'output_w': width,
            'background': [row[:side] for row in g[side:]],
            'foreground': [row[side:] for row in g[side:]]}


def background_field(g, mode='stretch'):
    if mode not in MODES:
        raise ValueError('Unknown background mode')
    view = analyze(g)
    n, height, width = view['side'], view['output_h'], view['output_w']
    background = view['background']
    return [[background[r * n // height if mode == 'stretch' else r % n]
                       [c * n // width if mode == 'stretch' else c % n]
             for c in range(width)] for r in range(height)]


def solve(g, mode='stretch'):
    view = analyze(g)
    field = background_field(g, mode)
    n = view['side']
    for r, row in enumerate(field):
        for c in range(len(row)):
            color = view['foreground'][r % n][c % n]
            if color:
                field[r][c] = color
    return field


def _background(rng, side, pattern):
    palette = rng.sample(range(1, 10), rng.randint(2, min(5, side * side)))
    phase = rng.randrange(len(palette))
    if pattern == 0:
        return [[palette[(r + phase) % len(palette)] for c in range(side)] for r in range(side)]
    if pattern == 1:
        return [[palette[(c + phase) % len(palette)] for c in range(side)] for r in range(side)]
    if pattern == 2:
        return [[palette[(r + c + phase) % len(palette)] for c in range(side)] for r in range(side)]
    if pattern == 3:
        return [[palette[(2 * (r >= side // 2) + (c >= side // 2) + phase) % len(palette)]
                 for c in range(side)] for r in range(side)]
    return [[rng.choice(palette) for c in range(side)] for r in range(side)]


def _foreground(rng, side, pattern):
    palette = rng.sample(range(1, 10), 3)
    result = []
    for r in range(side):
        row = []
        for c in range(side):
            visible = (rng.random() < .45 if pattern == 0 else
                       (r + c) % 2 == 0 if pattern == 1 else
                       (r in (0, side - 1) or c in (0, side - 1)) if pattern == 2 else
                       (r == c or r + c == side - 1))
            row.append(rng.choice(palette) if visible else 0)
        result.append(row)
    positions = rng.sample([(r, c) for r in range(side) for c in range(side)], 4)
    for r, c in positions[:2]:
        result[r][c] = 0
    for (r, c), value in zip(positions[2:], palette):
        result[r][c] = value
    return result


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    integer(seed, 'seed')
    integer(sample_index, 'sample_index')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('Unknown difficulty')
    if set(overrides) - set(AXES):
        raise ValueError('Unknown generator axis')
    rng = random.Random(int.from_bytes(hashlib.sha256(f'f931:{VERSION}:{seed}:{sample_index}'.encode()).digest(), 'big'))
    side = integer(overrides.get('quadrant_side', rng.randint(2, 15)), 'quadrant_side', 2, 15)
    choices = list(range(side, min(30, side * side) + 1, side))
    height = integer(overrides.get('output_h', rng.choice(choices)), 'output_h', 1, 30)
    width = integer(overrides.get('output_w', rng.choice(choices)), 'output_w', 1, 30)
    if height not in choices or width not in choices:
        raise ValueError('Fresh nonuniform backgrounds require feasible integer stretch factors')
    if height == width == side and not {'output_h', 'output_w'} & set(overrides):
        height = choices[-1]
    g = [[0] * (2 * side) for _ in range(2 * side)]
    for offset, count in ((0, height), (side, width)):
        positions = rng.sample([(r, c + offset) for r in range(side) for c in range(side)], count)
        for r, c in positions:
            g[r][c] = rng.randrange(1, 10)
    for attempt in range(64):
        # A stripe direction can hide a one-axis resize. Try another lawful
        # background pattern instead of retrying an impossible fixed pattern.
        bg = _background(rng, side, (sample_index + attempt) % 5)
        fg = _foreground(rng, side, sample_index % 4)
        for r in range(side):
            g[side + r] = bg[r] + fg[r]
        stretch = solve(g, 'stretch')
        repeat = solve(g, 'repeat')
        field = background_field(g, 'stretch')
        differences = sum(a != b for ar, br in zip(stretch, repeat) for a, b in zip(ar, br))
        overwritten = sum(a != b for ar, br in zip(stretch, field) for a, b in zip(ar, br))
        visible_background = {field[r][c] for r in range(height) for c in range(width) if fg[r % side][c % side] == 0}
        if (differences >= 2 or height == width == side) and overwritten >= 2 and len(visible_background) >= 2:
            return g
    raise ValueError('Bounded sampler could not expose both composition stages')


def self_check(grid, *, difficulty=None):
    try:
        analyze(grid)
        return []
    except (ValueError, TypeError, IndexError) as error:
        return [str(error)]
