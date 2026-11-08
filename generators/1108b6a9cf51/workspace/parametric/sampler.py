"""Deterministic, settings-independent inputs for native transform transfer.

Three mandatory examples teach a quarter-turn, an axis reflection and a
diagonal reflection. Separate streams build complete demonstration/query banks
before prefix slicing. All generated panel colors are individually connected.
"""
import hashlib
from pathlib import Path
import random

from reviewer_support import load_selected_generator

_selected, _source, _source_sha256 = load_selected_generator(
    '1108b6a9cf51', root=Path(__file__).resolve().parents[4])
_NAMES = _selected.TRANSFORMS
_OPPOSITE = {'rotate_cw': 'rotate_ccw', 'rotate_ccw': 'rotate_cw'}


def _rng(seed, role):
    key = f'1108b6a9cf51:native:v1:{seed}:{role}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), 'big'))


def _palette(rng, a_count, c_count):
    a = rng.sample(range(1, 9), a_count)
    pool = ([v for v in range(1, 9) if v not in a]
            if rng.randrange(2) else list(range(1, 9)))
    return a, rng.sample(pool, c_count)


def _panel(rng, size, colors, count):
    """Reuse clustered construction, with a total connected fallback.

    The fallback's first color occupies a proper top-edge prefix of at least
    two cells, which has no D4 stabilizer. If that prefix has one cell, all
    colors are singletons and the first two distinguish adjacent positions.
    Every remaining color is a contiguous segment of the same snake path.
    """
    if (not 3 <= size <= 9 or not 2 <= len(colors) <= 8
            or len(set(colors)) != len(colors)
            or any(type(v) is not int or not 1 <= v <= 8 for v in colors)
            or not len(colors) <= count < size * size):
        raise ValueError('unsupported clustered-panel request')
    for _ in range(32):
        panel = _selected._clustered_panel(rng, size, colors, count)
        if _selected._orbit_size(panel) == 8:
            return panel
    path = [(r, c) for r in range(size)
            for c in (range(size) if r % 2 == 0 else range(size - 1, -1, -1))]
    head = min(size - 1, count - len(colors) + 1)
    remaining = count - head
    cuts = sorted(rng.sample(range(1, remaining), len(colors) - 2))
    bounds = [0, head] + [head + v for v in cuts] + [count]
    panel = [[0] * size for _ in range(size)]
    for color, start, stop in zip(colors, bounds, bounds[1:]):
        for r, c in path[start:stop]:
            panel[r][c] = color
    return _selected._xform(panel, rng.choice(_NAMES))


def _relabel(panel, colors):
    return [[colors[value - 1] if value else 0 for value in row] for row in panel]


def _join(a, transform, c):
    b = _selected._xform(a, transform)
    return [left[:] + [9] + middle[:] + [9] + right[:]
            for left, middle, right in zip(a, b, c)]


def _ordinary(rng, size, transform, a_count, c_count, a_colors=3, c_colors=3):
    aa, cc = _palette(rng, a_colors, c_colors)
    return _join(_panel(rng, size, aa, a_count), transform,
                 _panel(rng, size, cc, c_count))


def sample_inputs(seed, demos=3, queries=4):
    """Return fresh grid banks for exact seed/count requests within the contract."""
    for value, low, high, name in ((seed, 0, 2**63 - 1, 'seed'),
                                   (demos, 3, 6, 'demos'), (queries, 1, 4, 'queries')):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    dr = _rng(seed, 'demonstrations')
    qr = _rng(seed, 'queries')
    quarter = _rng(seed, 'relation').choice(('rotate_cw', 'rotate_ccw'))

    aa, cc = _palette(dr, 5, 2)
    key = min(aa)
    colors = [key] + [color for color in aa if color != key]
    # Occupancy is D4 invariant; the lowest and uniquely rarest color is the
    # fixed center. The four distinct arms are needed to infer the quarter-turn.
    cross = _relabel([[0, 0, 2, 0, 0], [0, 0, 2, 0, 0],
                      [3, 3, 1, 4, 4], [0, 0, 5, 0, 0],
                      [0, 0, 5, 0, 0]], colors)
    cross = _selected._xform(cross, dr.choice(_NAMES))
    first = _join(cross, quarter, _panel(dr, 5, cc, dr.choice((8, 11))))

    aa, cc = _palette(dr, 3, 3)
    axis = dr.choice(('flip_lr', 'flip_ud'))
    sensitive = [[0, 1, 1, 0], [2, 1, 1, 3], [0, 1, 1, 0], [0, 0, 0, 0]]
    if axis == 'flip_ud':
        sensitive = _selected._xform(sensitive, 'transpose')
    small = [[0, 1, 2, 0], [0, 3, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    small = _selected._xform(_relabel(small, cc), dr.choice(_NAMES))
    second = _join(_relabel(sensitive, aa), axis, small)

    n = dr.choice((5, 6))
    diagonal = dr.choice(('transpose', 'anti_transpose'))
    third = _ordinary(dr, n, diagonal, round(.4 * n * n), round(.65 * n * n),
                      dr.randint(2, 4), dr.randint(2, 4))
    other_n = 11 - n
    train = [first, second, third,
             _ordinary(dr, 3, 'identity', 4, 5, 2, 2),
             _ordinary(dr, 4, 'rotate_180', 10, 6, 3, 2),
             _ordinary(dr, other_n, _OPPOSITE[quarter], round(.7 * other_n**2),
                       round(.35 * other_n**2), dr.randint(2, 4), dr.randint(2, 3))]

    test = [
        _ordinary(qr, 3, _OPPOSITE[quarter], qr.choice((4, 5)), qr.choice((4, 5)), 2, 2),
        _ordinary(qr, 7, 'identity', 18, 29, 4, 3),
        _ordinary(qr, 8, 'rotate_180', 43, 22, 3, 4),
        _ordinary(qr, 9, qr.choice(('flip_lr', 'flip_ud', 'transpose', 'anti_transpose')),
                  73, 73, 4, 4),
    ]
    _rng(seed, 'query-order').shuffle(test)
    return train[:demos], test[:queries]
