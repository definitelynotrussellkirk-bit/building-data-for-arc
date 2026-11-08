"""Constructive native orbit lessons with matched source-side demonstrations.

All four source sides are taught in the mandatory four-example prefix.  Each
matched pair keeps the canvas, anchor, template and palette fixed, changing only
the source position.  Complete six-demo/four-query banks precede count slicing.
The query side plan and complete-bank permutation have separate local streams.

The 6x6 minimum and dense 30x30/14x14 maximum can place their source only above or
left under the conservative anchor margin and one-blank-cell separation.  The
two middle-sized queries supply right and below, so each four-query bank still
covers all four sides.  Placement is constructive; there are no retry loops.
"""
from __future__ import annotations

import hashlib
import random


SIDES = ('above', 'right', 'below', 'left')
MAX_SEED = 2**63 - 1


def _check_seed(seed):
    if type(seed) is not int:
        raise TypeError('seed must be an exact integer')
    if not 0 <= seed <= MAX_SEED:
        raise ValueError('seed must be in 0..2**63-1')


def _check_count(value, name, minimum, maximum):
    if type(value) is not int:
        raise TypeError(f'{name} must be an exact integer')
    if not minimum <= value <= maximum:
        raise ValueError(f'{name} must be in {minimum}..{maximum}')


def _rng(seed, role):
    key = f'9a35b20efa99/native-orbit/v1/{seed}/{role}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), 'big'))


def _normalize(cells):
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _rotate(cells, turns):
    result = _normalize(cells)
    for _ in range(turns):
        result = _normalize({(c, -r) for r, c in result})
    return result


def _transform(cells, rng, turns=(0, 1, 2, 3)):
    if rng.randrange(2):
        cells = {(r, -c) for r, c in cells}
    return _rotate(cells, rng.choice(turns))


def _size(cells):
    return max(r for r, c in cells) + 1, max(c for r, c in cells) + 1


def _source_bounds(height, width, shape, anchor, side):
    h, w = shape
    ar, ac = anchor
    if side == 'above':
        return 0, ar - h - 1, max(0, ac - w + 1), min(ac, width - w)
    if side == 'right':
        return max(0, ar - h + 1), min(ar, height - h), ac + 2, width - w
    if side == 'below':
        return ar + 2, height - h, max(0, ac - w + 1), min(ac, width - w)
    if side == 'left':
        return max(0, ar - h + 1), min(ar, height - h), 0, ac - w - 1
    raise ValueError('unknown source side')


def _can_place(height, width, shape, anchor, side):
    r0, r1, c0, c1 = _source_bounds(height, width, shape, anchor, side)
    return r0 <= r1 and c0 <= c1


def _anchor(height, width, cells, sides, rng, *, off_center=False):
    shape = _size(cells)
    m = max(shape)
    candidates = [(r, c)
                  for r in range(m + 1, height - m)
                  for c in range(m + 1, width - m)
                  if all(_can_place(height, width, shape, (r, c), side) for side in sides)]
    if off_center:
        candidates = [point for point in candidates if point != (height // 2, width // 2)]
    if not candidates:
        raise ValueError('constructor profile has no legal anchor')
    return rng.choice(candidates)


def _grid(height, width, cells, anchor, side, color, rng):
    r0, r1, c0, c1 = _source_bounds(height, width, _size(cells), anchor, side)
    if r0 > r1 or c0 > c1:
        raise ValueError('constructor profile has no legal source position')
    sr, sc = rng.randint(r0, r1), rng.randint(c0, c1)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[anchor[0]][anchor[1]] = 9
    for r, c in cells:
        grid[sr + r][sc + c] = color
    return grid


def _frame(height, width):
    return {(r, c) for r in range(height) for c in range(width)
            if r in (0, height - 1) or c in (0, width - 1)}


def _mandatory(seed):
    first = _rng(seed, 'demo-pair-a')
    branch = {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)}
    if first.randrange(2):
        branch.add((2, 2))
    branch = _transform(branch, first)
    ah, aw = first.randint(12, 15), first.randint(13, 16)
    aa = _anchor(ah, aw, branch, ('above', 'right'), first, off_center=True)
    color_a = first.randint(1, 8)

    second = _rng(seed, 'demo-pair-b')
    bh = second.choice((4, 5))
    ring = _frame(bh, 6)
    ring.remove((bh - 1, 5))
    ring.add((1, 1))
    ring = _transform(ring, second)
    hh, ww = second.randint(16, 18), second.randint(17, 19)
    ba = _anchor(hh, ww, ring, ('below', 'left'), second, off_center=True)
    color_b = second.choice([color for color in range(1, 9) if color != color_a])
    return [
        _grid(ah, aw, branch, aa, 'above', color_a, _rng(seed, 'demo-above')),
        _grid(ah, aw, branch, aa, 'right', color_a, _rng(seed, 'demo-right')),
        _grid(hh, ww, ring, ba, 'below', color_b, _rng(seed, 'demo-below')),
        _grid(hh, ww, ring, ba, 'left', color_b, _rng(seed, 'demo-left')),
    ]


def _optional(seed, index):
    rng = _rng(seed, f'demo-optional-{index}')
    if index == 0:
        cells = {(r, 1) for r in range(7)} | {(0, 0), (1, 2), (3, 0), (5, 2), (6, 0), (6, 2)}
        height, width = 17, 19
    else:
        steps = {(r, c) for r in range(4) for c in range(r + 1)}
        cells = {(2 * r + dr, 2 * c + dc) for r, c in steps for dr in range(2) for dc in range(2)}
        height, width = 19, 21
    cells = _transform(cells, rng)
    # Select from feasible side/anchor combinations, rather than retry a draw.
    shape, m = _size(cells), max(_size(cells))
    choices = [(side, (ar, ac)) for side in SIDES
               for ar in range(m + 1, height - m)
               for ac in range(m + 1, width - m)
               if _can_place(height, width, shape, (ar, ac), side)]
    side, anchor = rng.choice(choices)
    return _grid(height, width, cells, anchor, side, rng.randint(1, 8), rng)


def _query(seed, role, side):
    rng = _rng(seed, f'query-role-{role}')
    if role == 0:
        height, width = 6, 6
        cells = {(0, 0), (1, 0), (1, 1)}
    elif role == 1:
        height, width = 18, 20
        cells = {(r, c) for r in range(6) for c in range(8)
                 if not (1 <= r <= 3 and 2 <= c <= 4)}
        cells -= {(0, 7), (1, 7)}
    elif role == 2:
        height, width = 25, 27
        cells = {(r, c) for r in range(10) for c in range(11)
                 if not (2 <= r <= 7 and 2 <= c <= 8)}
        cells -= {(9, 0), (8, 0)}
    else:
        height, width = 30, 30
        cells = {(r, c) for r in range(14) for c in range(14)
                 if not (3 <= r <= 9 and 3 <= c <= 9)}
        cells -= {(0, 11), (0, 12), (0, 13), (1, 12), (1, 13), (2, 13), (11, 2)}
    # On the 18-row canvas a below source must keep its shorter axis vertical.
    turns = (0, 2) if role == 1 and side == 'below' else (0, 1, 2, 3)
    cells = _transform(cells, rng, turns)
    anchor = _anchor(height, width, cells, (side,), rng)
    return _grid(height, width, cells, anchor, side, rng.randint(1, 8), rng)


def sample_banks(seed):
    """Return fresh complete six-demo/four-query banks for one exact seed."""
    _check_seed(seed)
    train = _mandatory(seed) + [_optional(seed, index) for index in range(2)]
    sides_rng = _rng(seed, 'query-side-plan')
    edge_sides = ['above', 'left']
    middle_sides = ['right', 'below']
    sides_rng.shuffle(edge_sides)
    sides_rng.shuffle(middle_sides)
    sides = [edge_sides[0], middle_sides[0], middle_sides[1], edge_sides[1]]
    test = [_query(seed, role, side) for role, side in enumerate(sides)]
    _rng(seed, 'query-permutation').shuffle(test)
    return {'train': train, 'test': test}


def generate_inputs(seed, demos=4, queries=4):
    """Construct the complete banks, then return independent requested prefixes."""
    _check_seed(seed)
    _check_count(demos, 'demos', 4, 6)
    _check_count(queries, 'queries', 1, 4)
    banks = sample_banks(seed)
    return {'train': banks['train'][:demos], 'test': banks['test'][:queries]}
