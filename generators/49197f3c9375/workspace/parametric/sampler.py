"""Constructive, seed-stable native inputs for singleton-region episodes.

The small literal bank specifies topology, not complete grids or labels. Each
role independently varies orientation, paired transforms, colors, spacing and
canvas size. Scaling changes the actual shapes rather than padding a small
scene. No search loop or external task source is required.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

from reviewer_support import load_selected_generator

HERE = Path(__file__).resolve().parent
_selected, _, _ = load_selected_generator('49197f3c9375', root=HERE.parents[3])

# Every thick-bank shape has area 12 and a 4x4 bounding box. In particular,
# choosing the only hollow or only interior-bearing object cannot identify the
# teaching target: each has structurally comparable distractors. The two hole
# shapes also share perimeter, interior count, orbit size and projection counts
# while remaining different D4 classes.
_THICK_ROWS = {
    'cross': ('0110', '1111', '1111', '0110'),
    'ring': ('1111', '1001', '1001', '1111'),
    'notch': ('0001', '0111', '1111', '1111'),
    'hole_a': ('1111', '1111', '1010', '1100'),
    'hole_b': ('1111', '1111', '1010', '0110'),
}
_THIN_ROWS = {
    'thin_a': ('111', '110', '010'),
    'thin_b': ('111', '101', '100'),
    'thin_c': ('111', '010', '110'),
}


def _cells(rows):
    return tuple((r, c) for r, row in enumerate(rows)
                 for c, value in enumerate(row) if value == '1')


_THICK = {name: _cells(rows) for name, rows in _THICK_ROWS.items()}
_THIN = {name: _cells(rows) for name, rows in _THIN_ROWS.items()}


def _rng(seed, role):
    digest = hashlib.sha256(f'49197f3c9375:native-inputs-v1:{seed}:{role}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _scaled(cells, scale):
    return tuple(sorted((r * scale + dr, c * scale + dc)
                        for r, c in cells
                        for dr in range(scale) for dc in range(scale)))


def _orientation(cells, rng):
    if rng.randrange(2):
        cells = _selected._reflect_lr(cells)
    return _selected._rotate(cells, rng.randrange(4))


def _anchors(length, count, extent, rng, edges=False):
    """Place equal-size boxes with at least one full background row/column."""
    slack = length - count * extent - (count - 1)
    if slack < 0:
        raise ValueError('scene dimensions cannot contain the requested objects')
    gaps = [0] * (count + 1)
    if edges:
        gaps[0] = rng.randrange(min(slack, 1) + 1)
        slack -= gaps[0]
        gaps[-1] = rng.randrange(min(slack, 1) + 1)
        slack -= gaps[-1]
        buckets = list(range(1, count))
    else:
        buckets = list(range(count + 1))
    for _ in range(slack):
        gaps[rng.choice(buckets)] += 1
    positions, current = [], gaps[0]
    for index in range(count):
        positions.append(current)
        current += extent + 1 + gaps[index + 1]
    return positions


def _scene(rng, *, target_name, count, scale, target_rank, palette,
           height, width, edges=False, pair_names=None, first_pair_relation='rotation'):
    bank = _THIN if target_name in _THIN else _THICK
    target = bank[target_name]
    available = [(name, cells) for name, cells in bank.items() if name != target_name]
    # Default first pairs are chiral, giving rotation-only and reflection-only
    # relations. The first teaching role explicitly includes a symmetric ring
    # to refute selecting the most symmetric object.
    available.sort(key=lambda entry: (not _selected._is_chiral(entry[1]), entry[0]))
    if pair_names is not None:
        available = [(name, bank[name]) for name in pair_names]
    pairs = []
    first_pair = ()
    for index, (_, cells) in enumerate(available[:(count - 1) // 2]):
        base = _orientation(cells, rng)
        if index == 0:
            if first_pair_relation == 'rotation':
                partner = _selected._nonidentity_rotation(base, rng)
            elif first_pair_relation == 'reflection':
                partner = _selected._reflected_orientation(base, rng)
            else:
                raise ValueError('first_pair_relation must be rotation or reflection')
            first_pair = (base, partner)
        elif index == 1 and _selected._is_chiral(base):
            partner = _selected._reflected_orientation(base, rng)
        else:
            partner = _orientation(base, rng)
        pairs.extend([base, partner])
    if len(pairs) != count - 1:
        raise ValueError('shape bank does not contain enough distinct classes')
    # Keep the two members separated in scan order. Labels depend on complete
    # D4 grouping; nearby repetition and a fixed unique color are not cues.
    rng.shuffle(pairs)
    if first_pair_relation == 'reflection':
        if target_rank == 0:
            raise ValueError('reflection teaching witness requires a nonfirst target')
        # A rotation-only rival must encounter a false singleton before the
        # real target. This guard affects only the explicitly requested role.
        if not any(cells in first_pair for cells in pairs[:target_rank]):
            witness = next(i for i, cells in enumerate(pairs) if cells in first_pair)
            pairs[0], pairs[witness] = pairs[witness], pairs[0]
    shapes = pairs[:]
    shapes.insert(target_rank, _orientation(target, rng))
    shapes = [_scaled(cells, scale) for cells in shapes]
    extent = 3 * scale if bank is _THIN else 4 * scale
    nrows = (count + 2) // 3
    rows = _anchors(height, nrows, extent, rng, edges=edges)
    columns = _anchors(width, 3, extent, rng, edges=edges)
    colors = rng.sample(range(1, 10), count if palette == 'distinct' else (2 if palette == 'reused' else 1))
    colors = [colors[index % len(colors)] for index in range(count)]
    grid = [[0] * width for _ in range(height)]
    for index, cells in enumerate(shapes):
        r0, c0 = rows[index // 3], columns[index % 3]
        for r, c in cells:
            grid[r0 + r][c0 + c] = colors[index]
    return grid


def _role(seed, role):
    rng = _rng(seed, role)
    if role == 'demo0':
        # hole_a is not first and shares every audited scalar descriptor with
        # hole_b. The ring pair has greater symmetry. Distinct colors make even
        # equal one-cell interior positions identify a wrong selected object.
        args = dict(target_name='hole_a', count=5, scale=1, target_rank=2,
                    palette='distinct', height=rng.randint(10, 14), width=rng.randint(17, 23),
                    pair_names=('hole_b', 'ring'), first_pair_relation='reflection')
    elif role == 'demo1':
        args = dict(target_name='ring', count=5, scale=2, target_rank=0,
                    palette='reused', height=rng.randint(20, 26), width=rng.randint(27, 30))
    elif role == 'demo2':
        args = dict(target_name='thin_a', count=5, scale=1, target_rank=4,
                    palette='monochrome', height=rng.randint(8, 12), width=rng.randint(15, 20))
    elif role == 'demo3':
        args = dict(target_name='hole_a', count=7, scale=1, target_rank=0,
                    palette='reused', height=rng.randint(16, 22), width=rng.randint(17, 24))
    elif role == 'demo4':
        args = dict(target_name='notch', count=9, scale=2, target_rank=8,
                    palette='distinct', height=30, width=30, edges=True)
    elif role == 'demo5':
        args = dict(target_name='hole_b', count=7, scale=1, target_rank=3,
                    palette='monochrome', height=rng.randint(17, 22), width=rng.randint(17, 24))
    elif role == 'query0':
        args = dict(target_name='thin_b', count=5, scale=1, target_rank=2,
                    palette='distinct', height=8, width=15)
    elif role == 'query1':
        args = dict(target_name='cross', count=7, scale=1, target_rank=rng.randrange(7),
                    palette='reused', height=rng.randint(17, 25), width=rng.randint(19, 29))
    elif role == 'query2':
        args = dict(target_name='ring', count=9, scale=2, target_rank=4,
                    palette='monochrome', height=30, width=30, edges=True)
    elif role == 'query3':
        args = dict(target_name=rng.choice(('cross', 'hole_a', 'hole_b')), count=9,
                    scale=2, target_rank=rng.randrange(9), palette='distinct',
                    height=30, width=30, edges=True)
    else:
        raise ValueError('unknown native role')
    return _scene(rng, **args)


def sample_inputs(seed, demos=3, queries=4):
    """Return fresh (demonstration inputs, query inputs), independent of settings.

    Accepted counts are exactly 3..6 demonstrations and 1..4 queries; a seed is
    an exact integer in 0..2**63-1. Each role has its own SHA-256-derived stream,
    and complete banks are generated before slicing, preserving both prefixes.
    """
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError('seed must be an integer in 0..2**63-1')
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError('demos must be an integer in 3..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an integer in 1..4')
    train = [_role(seed, f'demo{index}') for index in range(6)]
    test = [_role(seed, f'query{index}') for index in range(4)]
    return train[:demos], test[:queries]
