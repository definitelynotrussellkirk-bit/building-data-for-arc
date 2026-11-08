"""Independent coordinate, canonical, strict-domain and protected-rule checks."""
import importlib.util

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / 'generators/1108b6a9cf51/workspace/parametric'
NAMES = ('identity', 'rotate_cw', 'rotate_180', 'rotate_ccw',
         'flip_lr', 'flip_ud', 'transpose', 'anti_transpose')
MODES = ('forward', 'inverse', 'twice')
A = [[1, 1, 2], [3, 0, 2], [3, 4, 4]]
C = [[5, 0, 6], [0, 5, 0], [7, 0, 0]]


def family():
    path = HOME / 'native_family.py'
    assert path.is_file(), 'native family not yet implemented'
    spec = importlib.util.spec_from_file_location('native_transfer_family_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transform(grid, name):
    n = len(grid)
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
    lookup = coordinates[name]
    return [[grid[lookup(r, c)[0]][lookup(r, c)[1]] for c in range(n)] for r in range(n)]


def scene(name, a=A, c=C):
    b = transform(a, name)
    return [left[:] + [9] + middle[:] + [9] + right[:]
            for left, middle, right in zip(a, b, c)]


def expected(c, name, mode):
    if mode == 'inverse':
        name = {'rotate_cw': 'rotate_ccw', 'rotate_ccw': 'rotate_cw'}.get(name, name)
    result = transform(c, name)
    return transform(result, name) if mode == 'twice' else result


@pytest.mark.parametrize('name', NAMES)
@pytest.mark.parametrize('mode', MODES)
def test_every_operator_and_transfer_power_against_coordinates(name, mode):
    f = family(); grid = scene(name); before = [r[:] for r in grid]
    info = f.validate_grid(grid)
    assert info['inferred'] == name and info['code'] == NAMES.index(name) + 1
    actual = f.apply(grid, {'transfer': mode})
    assert actual == expected(C, name, mode)
    actual[0][0] = 9
    assert grid == before
    assert f.apply(grid, {'transfer': mode}) == expected(C, name, mode)


def test_all_operators_and_settings_execute_through_protected_racket():
    f = family()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        assert identity['protected'] and identity['backend'] == 'racket'
        for mode in MODES:
            for name in NAMES:
                assert apply(f.program({'transfer': mode}), scene(name)) == expected(C, name, mode)
    finally:
        bridge.close()


def test_exact_selected_default_and_all_five_canonical_pairs():
    f = family()
    from arcpuzzles import Catalog
    from arcpuzzles.parametric_worker import _real_evaluator
    record = Catalog(ROOT).get('1108b6a9cf51'); count = 0
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    def integers(grid):
        return [[int(v) for v in row] for row in grid]
    try:
        for variant in record['variants']:
            assert f.program({'transfer': 'forward'}) == variant['program_solution']
            tests = variant.get('test', [])
            if isinstance(tests, dict): tests = [tests]
            for pair in variant.get('train', []) + tests:
                if 'output' not in pair: continue
                grid, output = integers(pair['input']), integers(pair['output'])
                assert f.apply(grid, {'transfer': 'forward'}) == output
                assert apply(f.program({'transfer': 'forward'}), grid) == output
                count += 1
    finally:
        bridge.close()
    assert count == 5


def test_native_size_nine_is_substantive_and_cannot_be_padded_to_thirty_square():
    f = family(); a = [[0] * 9 for _ in range(9)]; c = [[0] * 9 for _ in range(9)]
    for r in range(9):
        for col in range(9):
            if r < 8:
                a[r][col] = 1 if col < 5 else 2
                c[r][col] = 3 if r < 5 else 4
    a[8][0] = 1; c[8][8] = 5
    g = scene('rotate_ccw', a, c)
    assert f.validate_grid(g)['size'] == 9
    assert len(g) == 9 and len(g[0]) == 29
    assert sum(v != 0 for row in c for v in row) == 73
    assert f.apply(g, {'transfer': 'forward'}) == transform(c, 'rotate_ccw')
    with pytest.raises(ValueError):
        f.validate_grid(g + [[0] * 29])


@pytest.mark.parametrize('settings', [None, [], {}, {'transfer': 1}, {'transfer': True},
    {'transfer': 'bad'}, {'transfer': 'forward', 'extra': 0}])
def test_strict_settings(settings):
    f = family()
    with pytest.raises(ValueError): f.program(settings)
    with pytest.raises(ValueError): f.apply(scene('transpose'), settings)


@pytest.mark.parametrize('mutation', ['bool', 'float', 'negative', 'too_large', 'ragged',
    'missing_separator', 'extra_separator_color', 'non_square', 'symmetric_a',
    'symmetric_c', 'no_matching_b', 'empty', 'tuple'])
def test_strict_grid_grammar(mutation):
    f = family(); g = scene('rotate_cw')
    if mutation == 'bool': g[0][0] = True
    elif mutation == 'float': g[0][0] = 1.0
    elif mutation == 'negative': g[0][0] = -1
    elif mutation == 'too_large': g[0][0] = 10
    elif mutation == 'ragged': g[0].pop()
    elif mutation == 'missing_separator': g[0][3] = 0
    elif mutation == 'extra_separator_color': g[1][0] = 9
    elif mutation == 'non_square': g.append(g[-1][:])
    elif mutation == 'symmetric_a': g = scene('identity', [[1, 0, 1], [0, 0, 0], [1, 0, 1]])
    elif mutation == 'symmetric_c': g = scene('rotate_cw', c=[[0, 0, 0], [0, 5, 0], [0, 0, 0]])
    elif mutation == 'no_matching_b': g[0][4] = 8
    elif mutation == 'empty': g = []
    elif mutation == 'tuple': g = tuple(g)
    with pytest.raises(ValueError): f.validate_grid(g)


def test_wrong_inferred_operation_is_a_real_output_counterfactual():
    f = family(); grid = scene('rotate_cw')
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, _, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        proper = apply(f.program({'transfer': 'forward'}), grid)
        wrong = apply(f.variant_program({'transfer': 'forward'}, code_expression='1'), grid)
        assert wrong == C and wrong != proper
    finally:
        bridge.close()
