"""Independent geometry checks for the native three-panel input curriculum."""
import importlib.util
import hashlib
import json
import random

import pytest
from reviewer_support import find_root

HOME = find_root(__file__) / 'generators/1108b6a9cf51/workspace/parametric'
NAMES = ('identity', 'rotate_cw', 'rotate_180', 'rotate_ccw',
         'flip_lr', 'flip_ud', 'transpose', 'anti_transpose')


def sampler():
    path = HOME / 'sampler.py'
    assert path.is_file(), 'native sampler has not been implemented'
    spec = importlib.util.spec_from_file_location('_native_transfer_sampler_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transform(panel, name):
    n = len(panel)
    coordinates = {
        'identity': lambda r, c: (r, c),
        'rotate_cw': lambda r, c: (n - 1 - c, r),
        'rotate_180': lambda r, c: (n - 1 - r, n - 1 - c),
        'rotate_ccw': lambda r, c: (c, n - 1 - r),
        'flip_lr': lambda r, c: (r, n - 1 - c),
        'flip_ud': lambda r, c: (n - 1 - r, c),
        'transpose': lambda r, c: (c, r),
        'anti_transpose': lambda r, c: (n - 1 - c, n - 1 - r),
    }
    locate = coordinates[name]
    return [[panel[locate(r, c)[0]][locate(r, c)[1]]
             for c in range(n)] for r in range(n)]


def candidates(a, b):
    return [name for name in NAMES if transform(a, name) == b]


def connected(panel, color):
    pending = {(r, c) for r, row in enumerate(panel)
               for c, value in enumerate(row) if value == color}
    if not pending:
        return False
    reached = {pending.pop()}
    queue = list(reached)
    while queue:
        r, c = queue.pop()
        for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if p in pending:
                pending.remove(p)
                reached.add(p)
                queue.append(p)
    return not pending


def inspect(grid):
    n = len(grid)
    assert type(grid) is list and 3 <= n <= 9
    assert all(type(row) is list and len(row) == 3 * n + 2 for row in grid)
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    assert all(row[n] == row[2 * n + 1] == 9 for row in grid)
    panels = [[row[start:start + n] for row in grid]
              for start in (0, n + 1, 2 * n + 2)]
    assert all(v != 9 for p in panels for row in p for v in row)
    colors = {v for p in (panels[0], panels[2]) for row in p for v in row if v}
    assert 2 <= len(colors) <= 8
    for p in (panels[0], panels[2]):
        values = {v for row in p for v in row}
        assert 0 in values and len(values) > 1
        assert len({json.dumps(transform(p, name)) for name in NAMES}) == 8
        assert all(connected(p, color) for color in values if color)
    matches = candidates(panels[0], panels[1])
    assert len(matches) == 1
    return panels, matches[0]


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_minimum_lesson_teaches_operation_families_and_color_sensitive_inference(seed):
    train, _ = sampler().sample_inputs(seed)
    assert len(train) == 3
    parsed = [inspect(grid) for grid in train]
    assert parsed[0][1] in ('rotate_cw', 'rotate_ccw')
    assert parsed[1][1] in ('flip_lr', 'flip_ud')
    assert parsed[2][1] in ('transpose', 'anti_transpose')
    assert [len(grid) for grid in train[:2]] == [5, 4]
    assert len(train[2]) in (5, 6)
    # D1's shape alone gives no orientation information, for every D4 operation.
    a, b, _ = parsed[0][0]
    mask_a = [[int(v != 0) for v in row] for row in a]
    mask_b = [[int(v != 0) for v in row] for row in b]
    assert len(candidates(mask_a, mask_b)) == 8
    # D2 requires minority colors: both occupancy and the dominant-color mask
    # admit identity, while the full colored panel requires a reflection.
    a, b, c = parsed[1][0]
    values = [v for row in a for v in row if v]
    counts = {v: values.count(v) for v in set(values)}
    dominant = max(counts, key=counts.get)
    assert list(counts.values()).count(counts[dominant]) == 1
    for project in (lambda v: int(v != 0), lambda v: int(v == dominant)):
        pa = [[project(v) for v in row] for row in a]
        pb = [[project(v) for v in row] for row in b]
        assert 'identity' in candidates(pa, pb)
        assert len(candidates(pa, pb)) > 1
    occupied = [(r, col) for r, row in enumerate(c) for col, v in enumerate(row) if v]
    assert max(r for r, col in occupied) - min(r for r, col in occupied) + 1 < 4
    assert max(col for r, col in occupied) - min(col for r, col in occupied) + 1 < 4


@pytest.mark.parametrize('seed', [0, 17, 19, 2**63 - 1])
def test_complete_bank_is_lawful_distinct_and_has_substantive_maximum_extent(seed):
    train, test = sampler().sample_inputs(seed, 6, 4)
    assert (len(train), len(test)) == (6, 4)
    assert len({json.dumps(g) for g in train + test}) == 10
    parsed = [inspect(g) for g in train + test]
    assert sorted(len(g) for g in test) == [3, 7, 8, 9]
    assert {name for panels, name in parsed} >= {'identity', 'rotate_180'}
    maximum = next(g for g in test if len(g) == 9)
    panels, _ = inspect(maximum)
    assert len(maximum[0]) == 29
    assert sum(v != 0 for row in maximum for v in row) == 237
    for panel in panels:
        assert sum(v != 0 for row in panel for v in row) == 73
        assert all(any(line) for line in (panel[0], panel[-1],
                   [row[0] for row in panel], [row[-1] for row in panel]))
    quarter = inspect(train[0])[1]
    small_query = next(g for g in test if len(g) == 3)
    assert inspect(small_query)[1] == {'rotate_cw': 'rotate_ccw',
                                      'rotate_ccw': 'rotate_cw'}[quarter]


def test_independent_counts_share_prefixes_of_the_same_full_banks():
    module = sampler()
    full = module.sample_inputs(17, 6, 4)
    for demos, queries in ((3, 1), (3, 4), (4, 2), (5, 3), (6, 1)):
        train, test = module.sample_inputs(17, demos, queries)
        assert train == full[0][:demos]
        assert test == full[1][:queries]


@pytest.mark.parametrize('seed', [0, 17, 19, 2**63 - 1])
def test_first_demo_refutes_rarest_and_lowest_color_selectors_in_all_modes(seed):
    train, _ = sampler().sample_inputs(seed)
    (a, b, c), quarter = inspect(train[0])
    assert len(a) == 5
    values = [v for row in a for v in row if v]
    counts = {v: values.count(v) for v in set(values)}
    assert sorted(counts.values()) == [1, 2, 2, 2, 2]
    key = min(counts)
    assert a[2][2] == key and counts[key] == 1
    assert min(counts, key=counts.get) == key
    assert quarter in ('rotate_cw', 'rotate_ccw')
    # Both saved shortcuts select the center singleton and infer identity.
    # Its mask, and the occupancy mask, are invariant under every D4 operator.
    for project in (lambda v: int(v != 0), lambda v: int(v == key)):
        pa = [[project(v) for v in row] for row in a]
        pb = [[project(v) for v in row] for row in b]
        assert candidates(pa, pb) == list(NAMES)
    inverse = {'rotate_cw': 'rotate_ccw', 'rotate_ccw': 'rotate_cw'}[quarter]
    intended = [transform(c, quarter), transform(c, inverse),
                transform(transform(c, quarter), quarter)]
    assert all(expected != c for expected in intended)


@pytest.mark.parametrize('seed,selector,mode', [
    (17, 'rarest', 'forward'), (17, 'rarest', 'inverse'),
    (17, 'rarest', 'twice'), (2**63 - 1, 'lowest', 'twice'),
])
def test_saved_color_shortcuts_are_refuted_by_visible_demonstrations(seed, selector, mode):
    def transfer(c, name):
        if mode == 'inverse':
            name = {'rotate_cw': 'rotate_ccw', 'rotate_ccw': 'rotate_cw'}.get(name, name)
        first = transform(c, name)
        return transform(first, name) if mode == 'twice' else first
    refutations = []
    for grid in sampler().sample_inputs(seed)[0]:
        (a, b, c), correct = inspect(grid)
        cells = [v for row in a for v in row if v]
        counts = {v: cells.count(v) for v in set(cells)}
        color = min(counts, key=lambda v: (counts[v], v)) if selector == 'rarest' else min(counts)
        ma = [[int(v == color) for v in row] for row in a]
        mb = [[int(v == color) for v in row] for row in b]
        wrong = candidates(ma, mb)[0]
        refutations.append(transfer(c, correct) != transfer(c, wrong))
    assert any(refutations), 'saved color-subset shortcut still fits every visible demonstration'


# Frozen original sampler 09c3dc79a62a2e2fc5ae6d4d7d85a5304ba13758cfee5bc495fbc4c37ddc6381.
# Exact ordered query-bank hashes were extracted before the demonstration repair.
@pytest.mark.parametrize('seed,expected', [
    (0, '72c8dae485bf85e65944dc5cdf0bf7238b458a124162347df7b33359f7b8229e'),
    (17, '410bbb46d44461eba310ef3b3f427034de2bc93813de4cf8b7a19f9bee34bef9'),
    (19, '43d21c53498b33a9f630c8b284bf73d6e8ca60aeea9313e882136fa98faa756f'),
    (2**63 - 1, '8c2ab356fe377affe38e6fc93f4f48c3c40f5ac8edb325f5b726ff1bcc2f7ff3'),
])
def test_demonstration_repair_preserves_original_ordered_query_banks(seed, expected):
    _, test = sampler().sample_inputs(seed, 6, 4)
    actual = hashlib.sha256(json.dumps(test, separators=(',', ':')).encode()).hexdigest()
    assert actual == expected


def test_fresh_returns_determinism_and_global_rng_isolation():
    module = sampler()
    state = random.getstate()
    original = module.sample_inputs(19)
    altered = module.sample_inputs(19)
    assert original == altered and state == random.getstate()
    altered[0][0][0][0] = 9
    altered[1][0][0][0] = 9
    assert original == module.sample_inputs(19)
    assert state == random.getstate()


def test_bounded_seed_set_varies_operator_palette_geometry_and_query_order():
    module = sampler()
    operations, palettes, orders, sizes, sharing = set(), set(), set(), set(), set()
    for seed in range(16):
        train, test = module.sample_inputs(seed, 6, 4)
        orders.add(tuple(len(g) for g in test))
        sizes.add(len(train[2]))
        for grid in train + test:
            panels, name = inspect(grid)
            operations.add(name)
            aa = {v for row in panels[0] for v in row if v}
            cc = {v for row in panels[2] for v in row if v}
            palettes.add(tuple(sorted(aa | cc)))
            sharing.add(bool(aa & cc))
    assert operations == set(NAMES)
    assert len(palettes) >= 12 and len(orders) >= 4
    assert sizes == {5, 6} and sharing == {False, True}


@pytest.mark.parametrize('seed', [True, 1.0, '1', None, -1, 2**63])
def test_seed_rejects_nonexact_or_out_of_range_values(seed):
    with pytest.raises((TypeError, ValueError)):
        sampler().sample_inputs(seed)


@pytest.mark.parametrize('demos', [2, 7, True, 3.0, None, '3'])
def test_demo_count_is_strict(demos):
    with pytest.raises((TypeError, ValueError)):
        sampler().sample_inputs(0, demos=demos)


@pytest.mark.parametrize('queries', [0, 5, False, 4.0, None, '4'])
def test_query_count_is_strict(queries):
    with pytest.raises((TypeError, ValueError)):
        sampler().sample_inputs(0, queries=queries)


def test_unknown_arguments_are_rejected():
    with pytest.raises(TypeError):
        sampler().sample_inputs(0, unknown=True)


@pytest.mark.parametrize('size,colors,count', [(3, [1, 2], 4),
    (5, [2, 3, 4, 5], 14), (9, [1, 3, 5, 7], 73)])
def test_exhausted_cluster_attempts_use_total_connected_asymmetric_fallback(monkeypatch, size, colors, count):
    module = sampler()
    calls = []
    def symmetric(rng, n, palette, occupied):
        calls.append(1)
        return [[0] * n for _ in range(n)]
    monkeypatch.setattr(module._selected, '_clustered_panel', symmetric)
    panel = module._panel(random.Random(7319), size, colors, count)
    assert 1 <= len(calls) <= 64
    assert sum(v != 0 for row in panel for v in row) == count
    assert {v for row in panel for v in row if v} == set(colors)
    assert len({json.dumps(transform(panel, name)) for name in NAMES}) == 8
    assert all(connected(panel, color) for color in colors)
    if size == 9:
        assert all(any(line) for line in (panel[0], panel[-1],
                   [row[0] for row in panel], [row[-1] for row in panel]))
