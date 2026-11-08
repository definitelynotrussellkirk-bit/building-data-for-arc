"""Literal geometry, exact canonical parity, strict inputs and causal checks."""
import importlib.util

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / 'generators/49197f3c9375/workspace/parametric'
MODES = ('boundary', 'whole', 'interior')
CROSS = ('0110', '1111', '1111', '0110')
RING = ('1111', '1001', '1001', '1111')
NOTCH = ('0001', '0111', '1111', '1111')
ELBOW = ('1110', '1000', '1000', '1100')


def family():
    path = HOME / 'native_family.py'
    assert path.is_file(), 'native family not implemented yet'
    spec = importlib.util.spec_from_file_location('native_singleton_family_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cells(rows, scale=1):
    return [(r * scale + dr, c * scale + dc)
            for r, row in enumerate(rows) for c, v in enumerate(row) if v == '1'
            for dr in range(scale) for dc in range(scale)]


def scene(rows=CROSS, scale=1, target_index=2):
    a, b = cells(NOTCH, scale), cells(ELBOW, scale)
    shapes = [a, [(r, 4 * scale - 1 - c) for r, c in a],
              b, [(c, 4 * scale - 1 - r) for r, c in b]]
    shapes.insert(target_index, cells(rows, scale))
    step = 4 * scale + 1
    h, w = 8 * scale + 1, max(15, 12 * scale + 2)
    g = [[0] * w for _ in range(h)]
    for i, shape in enumerate(shapes):
        top, left = (0 if i < 3 else step), (i % 3) * step
        for r, c in shape:
            g[top + r][left + c] = 7 if i == target_index else i + 1
    return g


def expected(rows, mode, scale=1):
    occupied = set(cells(rows, scale))
    interior = {p for p in occupied if all((p[0] + dr, p[1] + dc) in occupied
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))}
    chosen = occupied if mode == 'whole' else interior if mode == 'interior' else occupied - interior
    return [[7 if (r, c) in chosen else 0 for c in range(4 * scale)]
            for r in range(4 * scale)]


@pytest.mark.parametrize('mode', MODES)
@pytest.mark.parametrize('rows,scale', [(CROSS, 1), (RING, 1), (RING, 2)])
def test_component_regions_and_original_bbox(rows, scale, mode):
    f = family(); g = scene(rows, scale); before = [row[:] for row in g]
    result = f.apply(g, {'render': mode})
    assert result == expected(rows, mode, scale)
    result[0][0] = 9
    assert g == before and f.apply(g, {'render': mode}) == expected(rows, mode, scale)
    assert f.validate_grid(g)['target_rank'] == 2


def test_literal_cross_and_hole_interiors():
    f = family()
    assert f.apply(scene(), {'render': 'interior'}) == [
        [0, 0, 0, 0], [0, 7, 7, 0], [0, 7, 7, 0], [0, 0, 0, 0]]
    assert f.apply(scene(RING), {'render': 'interior'}) == [[0] * 4 for _ in range(4)]
    output = f.apply(scene(RING, 2), {'render': 'interior'})
    assert [(r, c) for r, row in enumerate(output) for c, v in enumerate(row) if v] == [
        (1, 1), (1, 6), (6, 1), (6, 6)]


def test_regions_execute_through_protected_racket():
    f = family()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        assert identity['protected'] and identity['backend'] == 'racket'
        for rows, scale in ((CROSS, 1), (RING, 1), (RING, 2)):
            for mode in MODES:
                assert apply(f.program({'render': mode}), scene(rows, scale)) == expected(rows, mode, scale)
    finally:
        bridge.close()


def test_exact_selected_default_and_three_canonical_pairs():
    f = family()
    from arcpuzzles import Catalog
    from arcpuzzles.parametric_worker import _real_evaluator
    record = Catalog(ROOT).get('49197f3c9375'); count = 0
    apply, _, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        for variant in record['variants']:
            assert f.program({'render': 'boundary'}) == variant['program_solution']
            tests = variant.get('test', [])
            if type(tests) is dict: tests = [tests]
            for pair in variant.get('train', []) + tests:
                if 'output' not in pair: continue
                g = [[int(v) for v in row] for row in pair['input']]
                output = [[int(v) for v in row] for row in pair['output']]
                assert f.apply(g, {'render': 'boundary'}) == output
                assert apply(f.program({'render': 'boundary'}), g) == output
                count += 1
    finally:
        bridge.close()
    assert count == 3


@pytest.mark.parametrize('settings', [None, [], {}, {'render': 1}, {'render': True},
    {'render': 'bad'}, {'render': 'boundary', 'extra': 0}])
def test_strict_settings(settings):
    f = family()
    with pytest.raises(ValueError): f.program(settings)
    with pytest.raises(ValueError): f.apply(scene(), settings)


@pytest.mark.parametrize('mutation', ['bool', 'float', 'negative', 'too_large', 'ragged',
    'height_small', 'height_large', 'width_small', 'width_large', 'empty', 'tuple',
    'missing_object', 'extra_object', 'two_singletons', 'unique_size'])
def test_strict_scene_grammar(mutation):
    f = family(); g = scene()
    if mutation == 'bool': g[0][0] = True
    elif mutation == 'float': g[0][0] = 1.0
    elif mutation == 'negative': g[0][0] = -1
    elif mutation == 'too_large': g[0][0] = 10
    elif mutation == 'ragged': g[0].pop()
    elif mutation == 'height_small': g = g[:7]
    elif mutation == 'height_large': g += [[0] * 15 for _ in range(31 - len(g))]
    elif mutation == 'width_small': g = [row[:14] for row in g]
    elif mutation == 'width_large': g = [row + [0] * (31 - len(row)) for row in g]
    elif mutation == 'empty': g = []
    elif mutation == 'tuple': g = tuple(g)
    elif mutation == 'missing_object':
        g = [[0 if v == 1 else v for v in row] for row in g]
    elif mutation == 'extra_object': g[8][14] = 9
    elif mutation == 'two_singletons': g[3][0] = 0
    elif mutation == 'unique_size': g[0][10] = 7
    with pytest.raises(ValueError): f.validate_grid(g)


def test_wrong_selected_component_changes_all_three_renderings():
    f = family(); g = scene()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, _, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        for mode in MODES:
            setting = {'render': mode}
            proper = apply(f.program(setting), g)
            wrong = apply(f.variant_program(setting, target_expression='(first objs)'), g)
            assert proper == expected(CROSS, mode) and wrong != proper
    finally:
        bridge.close()
