"""Fresh color-key panel erasure grammar and independent Python label mirror."""
from __future__ import annotations
import hashlib
import random

GENERATOR_ID = 'public_eval_d59b0160'
TASK_ID = GENERATOR_ID
RULE_TASK_ID = 'ee_d59b0160'
VERSION = '1.0.0'
SUMMARY = 'Read the framed color key, then erase panels containing all its colors.'
EXAMPLES_NEEDED = 2
INVARIANTS = ['one green L-frame around a nonempty color key', 'orange exterior and black panel fill',
              'rectangular panels separated by orange, possibly touching the canvas boundary']
AXES = {'grid_h': {'type': 'int', 'valid': '13..30', 'default': '13..30'},
        'grid_w': {'type': 'int', 'valid': '13..30', 'default': '13..30'},
        'key_count': {'type': 'int', 'valid': '2..4', 'default': '2..4'},
        'orientation': {'type': 'int', 'valid': '0..7', 'default': '0..7'}}
MODES = ('contains_all', 'contains_any', 'exact_palette')
COLORS = (1, 2, 4, 5, 6, 8, 9)


def integer(value, name, low=0, high=2**63 - 1):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def validate_grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
            or not 1 <= len(g[0]) <= 30
            or any(type(row) is not list or len(row) != len(g[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular exact-integer color grid, 1..30 by 1..30')


def cells_in(box):
    r0, c0, r1, c1 = box
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def components(cells):
    todo = set(cells)
    result = []
    while todo:
        start = min(todo)
        todo.remove(start)
        stack, part = [start], []
        while stack:
            r, c = stack.pop()
            part.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    q = r + dr, c + dc
                    if q in todo:
                        todo.remove(q)
                        stack.append(q)
        result.append(sorted(part))
    return result


def analyze(g):
    validate_grid(g)
    frame = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 3]
    if not frame:
        raise ValueError('Missing key frame')
    r0, c0 = min(r for r, c in frame), min(c for r, c in frame)
    r1, c1 = max(r for r, c in frame), max(c for r, c in frame)
    box = r0, c0, r1, c1
    possible = [{(rr, c) for c in range(c0, c1 + 1)} | {(r, cc) for r in range(r0, r1 + 1)}
                for rr in (r0, r1) for cc in (c0, c1)]
    if r1 == r0 or c1 == c0 or set(frame) not in possible:
        raise ValueError('Key frame must be an axis-aligned L')
    key_cells = set(cells_in(box))
    key = {g[r][c] for r, c in key_cells} - {3, 7}
    if not key or 0 in key:
        raise ValueError('Key must contain payload colors, not panel filler')
    panels = []
    for part in components((r, c) for r, row in enumerate(g) for c, v in enumerate(row)
                           if v != 7 and (r, c) not in key_cells):
        bounds = min(r for r, c in part), min(c for r, c in part), max(r for r, c in part), max(c for r, c in part)
        if len(cells_in(bounds)) != len(part):
            raise ValueError('Panel support must be a complete rectangle')
        panels.append({'box': bounds, 'cells': part, 'palette': {g[r][c] for r, c in part} - {0}})
    if not panels:
        raise ValueError('At least one panel is required')
    return {'key': key, 'key_box': box, 'panels': panels}


def selected(key, palette, mode):
    if mode == 'contains_all':
        return key <= palette
    if mode == 'contains_any':
        return bool(key & palette)
    if mode == 'exact_palette':
        return key == palette
    raise ValueError('Unknown match mode')


def solve(g, mode='contains_all'):
    if mode not in MODES:
        raise ValueError('Unknown match mode')
    view = analyze(g)
    out = [row[:] for row in g]
    for panel in view['panels']:
        if selected(view['key'], panel['palette'], mode):
            for r, c in panel['cells']:
                out[r][c] = 7
    return out


def transform(g, code):
    integer(code, 'orientation', 0, 7)
    out = [row[:] for row in g]
    if code & 4:
        out = [list(row) for row in zip(*out)]
    if code & 2:
        out = out[::-1]
    if code & 1:
        out = [row[::-1] for row in out]
    return out


def _partition(rng, boxes, count):
    boxes = list(boxes)
    while len(boxes) < count:
        choices = []
        for i, (r0, c0, r1, c1) in enumerate(boxes):
            for cut in range(r0 + 2, r1 - 1):
                if (cut - r0) * (c1 - c0 + 1) >= 8 and (r1 - cut) * (c1 - c0 + 1) >= 8:
                    choices.append((i, (r0, c0, cut - 1, c1), (cut + 1, c0, r1, c1)))
            for cut in range(c0 + 2, c1 - 1):
                if (cut - c0) * (r1 - r0 + 1) >= 8 and (c1 - cut) * (r1 - r0 + 1) >= 8:
                    choices.append((i, (r0, c0, r1, cut - 1), (r0, cut + 1, r1, c1)))
        if not choices:
            raise ValueError('Panel partition cannot satisfy requested geometry')
        i, left, right = rng.choice(choices)
        boxes[i:i + 1] = [left, right]
    return boxes


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    integer(seed, 'seed')
    integer(sample_index, 'sample_index')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('Unknown difficulty')
    if set(overrides) - set(AXES):
        raise ValueError('Unknown generator axis')
    rng = random.Random(int.from_bytes(hashlib.sha256(f'd59:{VERSION}:{seed}:{sample_index}'.encode()).digest(), 'big'))
    height = integer(overrides.get('grid_h', rng.randint(13, 30)), 'grid_h', 13, 30)
    width = integer(overrides.get('grid_w', rng.randint(13, 30)), 'grid_w', 13, 30)
    key_count = integer(overrides.get('key_count', rng.randint(2, 4)), 'key_count', 2, 4)
    code = integer(overrides.get('orientation', rng.randrange(8)), 'orientation', 0, 7)
    h, w = (width, height) if code & 4 else (height, width)
    side = rng.choice([s for s in (2, 3, 4) if s * s >= key_count + 1])
    key = rng.sample(COLORS, key_count)
    extras = [c for c in COLORS if c not in key]
    g = [[7] * w for _ in range(h)]
    for i in range(side + 1):
        g[side][i] = g[i][side] = 3
    slots = [(r, c) for r in range(side) for c in range(side)]
    rng.shuffle(slots)
    for (r, c), color in zip(slots, key + [rng.choice(key)]):
        g[r][c] = color
    count = rng.randint(5, 7) if min(h, w) < 20 else rng.randint(6, 9)
    boxes = _partition(rng, [(0, side + 2, h - 1, w - 1), (side + 2, 0, h - 1, side)], count)
    rng.shuffle(boxes)
    kinds = ['exact', 'superset', 'partial', 'disjoint', 'empty']
    kinds += [rng.choice(kinds) for _ in range(count - len(kinds))]
    for box, kind in zip(boxes, kinds):
        cells = cells_in(box)
        for r, c in cells:
            g[r][c] = 0
        if kind == 'exact':
            palette = key[:]
        elif kind == 'superset':
            palette = key + rng.sample(extras, rng.randint(1, min(len(extras), 2)))
        elif kind == 'partial':
            palette = rng.sample(key, key_count - 1)
            if rng.choice([True, False]):
                palette += [rng.choice(extras)]
        elif kind == 'disjoint':
            palette = rng.sample(extras, rng.randint(1, len(extras)))
        else:
            palette = []
        if palette:
            capacity = len(cells) - 1
            if len(palette) > capacity:
                raise ValueError('Panel too small for palette')
            tokens = palette + [rng.choice(palette) for _ in range(rng.randint(1, max(1, capacity // 3)))]
            tokens = tokens[:capacity]
            rng.shuffle(cells)
            for (r, c), value in zip(cells, tokens):
                g[r][c] = value
    result = transform(g, code)
    analyze(result)
    return result


def self_check(grid, *, difficulty=None):
    try:
        analyze(grid)
        return []
    except (ValueError, TypeError, IndexError) as error:
        return [str(error)]
