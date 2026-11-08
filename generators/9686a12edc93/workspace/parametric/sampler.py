"""Constructive endpoint lessons with independent complete demo/query banks.

Colors encode the canonical numeric processing order. Scene roles deliberately
vary crossing topology, clear/blocked paths, invalid multiplicities, and size.
Only inputs leave this module; no private scene descriptors enter challenges.
"""
import hashlib
import random


def _seed(seed):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError('seed must be an exact integer in 0..2**63-1')


def _rng(seed, role):
    digest = hashlib.sha256(f'9686a12edc93-native-v1:{seed}:{role}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _scene(height, width, groups):
    grid = [[0] * width for _ in range(height)]
    for color, points in groups:
        for row, col in points:
            if grid[row][col]:
                raise RuntimeError('constructive endpoint or distractor collision')
            grid[row][col] = color
    return grid


def _decorate(grid, rng, *, turns=None, padding=2):
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    turns = rng.randrange(4) if turns is None else turns
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
    extra_h, extra_w = rng.randrange(padding + 1), rng.randrange(padding + 1)
    row0, col0 = rng.randrange(extra_h + 1), rng.randrange(extra_w + 1)
    result = [[0] * (len(grid[0]) + extra_w) for _ in range(len(grid) + extra_h)]
    for r, row in enumerate(grid):
        result[row0 + r][col0:col0 + len(row)] = row
    return result


def _chain_lesson(rng):
    palette = rng.sample(range(1, 10), 8)
    a, b, c, d = sorted(palette[:4])
    e, f, g, h = palette[4:]
    ac, cc = rng.choice((2, 3)), rng.choice((6, 7))
    br = rng.choice((2, 3))
    return _scene(12, 14, [
        (a, ((0, ac), (rng.choice((4, 5)), ac))),
        (b, ((br, 0), (br, 8))),
        (c, ((0, cc), (rng.choice((6, 7)), cc))),
        # D crosses older accepted A, but not the more recent accepted C.
        # Retaining only the latest accepted path would wrongly accept D.
        (d, ((1, 0), (1, ac + 1))),
        (e, ((9, 0), (9, 6))), (f, ((9, 3),)),
        (g, ((8, 12), (10, 13))),
        # Off-span middle cell: first/last-of-three would draw a false path.
        (h, ((8, 10), (9, 12), (10, 10))),
    ])


def _priority_lesson(rng):
    palette = rng.sample(range(1, 10), 7)
    a, b = sorted(palette[:2])
    c, d = sorted(palette[2:4])
    e, f, g = palette[4:]
    crossing_col = rng.choice((4, 5))
    return _scene(11, 14, [
        # Lower color is horizontal and longer; its first endpoint is later
        # in reading order than the higher vertical pair's first endpoint.
        (a, ((3, 0), (3, 8))),
        (b, ((0, crossing_col), (6, crossing_col))),
        (c, ((8, 0), (8, 6))), (d, ((8, 3), (10, 3))),
        # Complementary off-span triple teaches nonpairs after odd rotations.
        (e, ((1, 11), (1, 13), (2, 12))),
        (f, ((3, 11), (5, 12))),
        (g, ((10, 7), (10, 8))),
    ])


def _clear_lesson(rng):
    a, b, c, d, e = rng.sample(range(1, 10), 5)
    return _scene(9, 12, [
        (a, ((0, 0), (0, 7))), (b, ((1, 10), (6, 10))),
        (c, ((3, 1), (3, 5))), (d, ((4, 7), (7, 7))),
        (e, ((8, 2), (8, 3))),
    ])


def _empty_lesson(rng):
    a, b, c, d, e = rng.sample(range(1, 10), 5)
    return _scene(9, 10, [
        (a, ((2, 0), (2, 4), (2, 8))), (b, ((6, 1),)),
        (c, ((0, 3), (5, 7))), (d, ((7, 1), (7, 7))),
        (e, ((7, 4),)),
    ])


def _mesh_lesson(rng):
    colors = rng.sample(range(1, 10), 6)
    groups = [(colors[i], ((r, 0), (r, 16))) for i, r in enumerate((3, 7, 11))]
    groups += [(colors[3 + i], ((0, c), (14, c))) for i, c in enumerate((4, 12))]
    groups += [(colors[5], ((14, 8),))]
    return _scene(15, 17, groups)


def _edge_lesson(rng):
    a, b, c, d, e, f = rng.sample(range(1, 10), 6)
    return _scene(16, 18, [
        (a, ((0, 1), (0, 16))), (b, ((15, 1), (15, 16))),
        (c, ((1, 0), (14, 0))), (d, ((1, 17), (14, 17))),
        (e, ((7, 3), (7, 14))), (f, ((3, 8), (12, 8))),
    ])


def _minimum_query(rng):
    a, b = rng.sample(range(1, 10), 2)
    return _scene(3, 3, [(a, ((0, 1), (2, 1))), (b, ((1, 0), (1, 2)))])


def _long_chain_query(rng):
    palette = rng.sample(range(1, 10), 8)
    a, b, c, d, e = sorted(palette[:5])
    f, g, h = palette[5:]
    return _scene(18, 20, [
        (a, ((1, 2), (7, 2))), (b, ((3, 0), (3, 8))),
        (c, ((0, 6), (12, 6))), (d, ((10, 4), (10, 14))),
        (e, ((8, 12), (15, 12))), (f, ((17, 2),)),
        (g, ((17, 8), (17, 10), (17, 12))),
        (h, ((6, 18), (14, 19))),
    ])


def _mixed_query(rng):
    a, b, c, d, e, f, g, h, i = rng.sample(range(1, 10), 9)
    return _scene(24, 26, [
        (a, ((3, 1), (3, 23))), (b, ((0, 5), (16, 5))),
        (c, ((12, 3), (12, 19))), (d, ((8, 17), (23, 17))),
        (e, ((20, 10), (20, 25))), (f, ((15, 11), (22, 11))),
        (g, ((6, 0), (6, 7))), (h, ((6, 2), (6, 4), (6, 6))),
        (i, ((21, 1), (23, 8))),
    ])


def _maximum_query(rng):
    colors = rng.sample(range(1, 10), 9)
    groups = [(colors[0], ((0, 0), (0, 29))), (colors[1], ((29, 0), (29, 29)))]
    rows = sorted(rng.sample(range(5, 25), 3))
    cols = sorted(rng.sample(range(3, 27), 4))
    groups += [(colors[2 + i], ((r, 1), (r, 28))) for i, r in enumerate(rows)]
    groups += [(colors[5 + i], ((2, c), (27, c))) for i, c in enumerate(cols)]
    return _scene(30, 30, groups)


def sample_banks(seed):
    """Return six fresh demonstrations and a complete shuffled query bank."""
    _seed(seed)
    turns = _rng(seed, 'mandatory-orientation').randrange(4)
    demos = []
    for index, builder in enumerate((_chain_lesson, _priority_lesson, _clear_lesson,
                                     _empty_lesson, _mesh_lesson, _edge_lesson)):
        rng = _rng(seed, 'demo-' + str(index))
        grid = builder(rng)
        demos.append(_decorate(grid, rng, turns=turns if index < 3 else None))
    queries = []
    for index, builder in enumerate((_minimum_query, _long_chain_query, _mixed_query, _maximum_query)):
        rng = _rng(seed, 'query-' + str(index))
        queries.append(_decorate(builder(rng), rng, padding=0))
    _rng(seed, 'query-order').shuffle(queries)
    return {'train': demos, 'test': queries}


def generate_inputs(seed, demos=3, queries=4):
    _seed(seed)
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError('demos must be an exact integer in 3..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an exact integer in 1..4')
    banks = sample_banks(seed)
    return {'train': banks['train'][:demos], 'test': banks['test'][:queries]}
