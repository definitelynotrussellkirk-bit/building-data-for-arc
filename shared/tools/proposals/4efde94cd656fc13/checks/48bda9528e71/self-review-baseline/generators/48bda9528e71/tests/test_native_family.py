"""Literal concave geometry, exact canonical parity and native-domain checks."""
import importlib.util

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / 'generators/48bda9528e71/workspace/parametric'
MODES = ('one_step', 'to_boundary')
SCENE = [[4, 4, 4, 4, 8], [4, 2, 4, 4, 8], [4, 4, 8, 8, 8],
         [4, 4, 8, 8, 8], [8, 8, 8, 8, 8]]
ANSWERS = {
    'one_step': [[8, 8, 8, 8, 2], [8, 8, 8, 8, 2], [8, 8, 2, 2, 8],
                 [8, 8, 2, 8, 8], [2, 2, 8, 8, 8]],
    'to_boundary': [[8, 8, 8, 8, 2], [8, 8, 8, 8, 2], [8, 8, 2, 2, 2],
                    [8, 8, 2, 2, 2], [2, 2, 2, 2, 8]],
}


def family():
    path = HOME / 'native_family.py'
    assert path.is_file(), 'native projection family not implemented yet'
    spec = importlib.util.spec_from_file_location('native_projection_family_test', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def transform(grid, code):
    result = [row[:] for row in grid]
    if code >= 4: result = [row[::-1] for row in result]
    for _ in range(code % 4):
        n = len(result); result = [[result[n - 1 - c][r] for c in range(n)] for r in range(n)]
    return result


@pytest.mark.parametrize('code', range(8))
@pytest.mark.parametrize('mode', MODES)
def test_literal_notch_and_all_orientations(code, mode):
    f = family(); g = transform(SCENE, code); before = [r[:] for r in g]
    actual = f.apply(g, {'projection_reach': mode})
    assert actual == transform(ANSWERS[mode], code)
    assert all(actual[r][c] == 8 for r, row in enumerate(g) for c, v in enumerate(row) if v != 8)
    actual[0][0] = 9
    assert g == before and f.apply(g, {'projection_reach': mode}) == transform(ANSWERS[mode], code)


def test_zero_is_a_valid_rare_foreground_color():
    f = family(); g = [[0 if v == 2 else v for v in row] for row in SCENE]
    for mode in MODES:
        assert f.apply(g, {'projection_reach': mode}) == [[0 if v == 2 else v for v in row] for row in ANSWERS[mode]]
    assert f.validate_grid(g)['rare_color'] == 0


def test_literal_labels_execute_in_protected_racket():
    f = family()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        assert identity['protected'] and identity['backend'] == 'racket'
        for mode in MODES:
            for code in range(8):
                assert apply(f.program({'projection_reach': mode}), transform(SCENE, code)) == transform(ANSWERS[mode], code)
    finally:
        bridge.close()


def test_default_is_exact_selected_source_and_all_six_canonical_labels():
    f = family()
    from arcpuzzles import Catalog
    from arcpuzzles.parametric_worker import _real_evaluator
    record = Catalog(ROOT).get('48bda9528e71'); count = 0
    apply, _, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        for variant in record['variants']:
            assert f.program({'projection_reach': 'one_step'}) == variant['program_solution']
            tests = variant.get('test', [])
            if type(tests) is dict: tests = [tests]
            for pair in variant.get('train', []) + tests:
                if 'output' not in pair: continue
                g = [[int(v) for v in row] for row in pair['input']]
                out = [[int(v) for v in row] for row in pair['output']]
                assert f.apply(g, {'projection_reach': 'one_step'}) == out
                assert apply(f.program({'projection_reach': 'one_step'}), g) == out
                count += 1
    finally:
        bridge.close()
    assert count == 6


@pytest.mark.parametrize('setting', [None, [], {}, {'projection_reach': 1},
    {'projection_reach': True}, {'projection_reach': 'bad'}, {'projection_reach': 'one_step', 'extra': 0}])
def test_strict_settings(setting):
    f = family()
    with pytest.raises(ValueError): f.program(setting)
    with pytest.raises(ValueError): f.apply(SCENE, setting)


@pytest.mark.parametrize('mutation', ['bool', 'float', 'negative', 'color10', 'empty',
    'tuple', 'row_tuple', 'ragged', 'small', 'large', 'nonsquare', 'one_color',
    'four_colors', 'rare_boundary', 'row_gap', 'extra_component'])
def test_strict_native_grammar(mutation):
    f = family(); g = [r[:] for r in SCENE]
    if mutation == 'bool': g[0][0] = True
    elif mutation == 'float': g[0][0] = 4.0
    elif mutation == 'negative': g[0][0] = -1
    elif mutation == 'color10': g[0][0] = 10
    elif mutation == 'empty': g = []
    elif mutation == 'tuple': g = tuple(g)
    elif mutation == 'row_tuple': g[0] = tuple(g[0])
    elif mutation == 'ragged': g[0].pop()
    elif mutation == 'small': g = [row[:4] for row in g[:4]]
    elif mutation == 'large': g = [[8] * 31 for _ in range(31)]
    elif mutation == 'nonsquare': g.append([8] * 5)
    elif mutation == 'one_color': g[1][1] = 4
    elif mutation == 'four_colors': g[0][0] = 1; g[0][1] = 3
    elif mutation == 'rare_boundary': g[1][1] = 4; g[0][0] = 2
    elif mutation == 'row_gap': g[0][1] = 8
    elif mutation == 'extra_component': g[4][4] = 4
    with pytest.raises(ValueError): f.validate_grid(g)


def test_full_span_thirty_uses_real_content_and_the_reused_projection_kernel():
    f = family(); g = [[4 if r < 7 or c < 9 else 8 for c in range(30)] for r in range(30)]
    g[2][20] = 0; g[20][2] = 0
    info = f.validate_grid(g)
    assert len(info['cells']) == 417 and info['rare_color'] == 0
    expected = [[8] * 30 for _ in range(30)]
    for r in range(7, 30):
        for c in range(9, 30): expected[r][c] = 0
    assert f.apply(g, {'projection_reach': 'to_boundary'}) == expected
    assert f._prototype.project_extents(g, 'to_boundary') == expected


def test_wrong_extent_tables_change_spatial_output_with_same_color_and_reach():
    f = family()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, _, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        for mode in MODES:
            setting = {'projection_reach': mode}
            correct = apply(f.program(setting), SCENE)
            wrong = apply(f.variant_program(setting, bbox_extents=True), SCENE)
            assert correct == ANSWERS[mode] and wrong != correct
            assert {v for row in wrong for v in row} <= {2, 8}
    finally:
        bridge.close()


def test_convexification_rival_uses_exact_lattice_hull_and_preserves_color_selection():
    f = family()
    hull = f._selected._lattice_convex_hull(f.validate_grid(SCENE)['cells'])
    assert (2, 2) in hull and SCENE[2][2] == 8
    convexified = [[4 if (r, c) in hull else 8 for c in range(5)] for r in range(5)]
    convexified[1][1] = 2
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, _, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        for mode in MODES:
            setting = {'projection_reach': mode}
            actual = apply(f.variant_program(setting, geometry='convex'), SCENE)
            assert actual == f._prototype.project_extents(convexified, mode)
            assert actual[2][2] == 8 and actual != ANSWERS[mode]
    finally:
        bridge.close()
