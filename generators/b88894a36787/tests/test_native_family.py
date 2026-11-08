"""Literal semantics and independent protected labels for route-then-fill."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
TASK = 'b88894a36787'
HOME = ROOT / 'generators' / TASK / 'workspace' / 'parametric'


def family():
    path = HOME / 'native_family.py'
    assert path.is_file(), 'native route/first-hit family has not been implemented'
    spec = importlib.util.spec_from_file_location('native_route_family_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene():
    grid = [[0] * 10 for _ in range(8)]
    grid[0][3:7] = [1, 2, 3, 4]
    grid[1][9] = 2
    grid[7][0] = 3
    return grid


EXPECTED_FIRST_HIT = [
    [0, 0, 0, 1, 2, 3, 4, 0, 0, 0],
    [0, 0, 0, 1, 2, 2, 2, 2, 2, 2],
    *[[0, 0, 0, 1, 0, 3, 0, 0, 0, 0] for _ in range(5)],
    [3, 3, 3, 3, 3, 3, 0, 0, 0, 0],
]


def test_literal_first_hit_preserves_blockers_and_priority_at_row_one_and_bottom():
    f = family()
    grid = scene()
    assert f.apply(grid, {'missing_extension': 'first_hit'}) == EXPECTED_FIRST_HIT
    assert f.first_hits(grid) == {3: 7, 6: 1}
    stage = f.render_matched(grid)
    assert stage[1][5] == 2  # Leftmost matched header wins its intersection.
    assert stage[7][3] == 3
    assert all(stage[r][3] == 0 for r in range(1, 7))


def test_bottom_and_penultimate_preserve_existing_exact_programs():
    f = family()
    spec = importlib.util.spec_from_file_location('legacy_route_program_test', HOME / 'missing_extension.py')
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    for mode in ('bottom', 'penultimate'):
        assert f.program({'missing_extension': mode}) == legacy.program_for(mode)
        assert f.apply(scene(), {'missing_extension': mode}) == legacy.apply_python(scene(), mode)
    assert f.program({'missing_extension': 'bottom'}).encode() == (HOME / 'canonical.rkt').read_bytes()


def test_no_hit_reaches_bottom_and_ignored_dots_disappear():
    f = family()
    grid = [[0] * 10 for _ in range(8)]
    grid[0][3:6] = [2, 4, 6]
    grid[2][0], grid[5][9], grid[3][0] = 2, 6, 9
    out = f.apply(grid, {'missing_extension': 'first_hit'})
    assert f.first_hits(grid) == {4: None}
    assert [row[4] for row in out] == [4] * 8
    assert out[3][0] == 0
    assert out == f.apply(grid, {'missing_extension': 'bottom'})
    assert f.apply(grid, {'missing_extension': 'penultimate'})[-1][4] == 0


def test_complete_input_is_setting_invariant_and_outputs_are_fresh():
    f = family()
    grid = scene()
    grid[3][0], grid[4][9] = 1, 4
    original = deepcopy(grid)
    outputs = [f.apply(grid, {'missing_extension': mode}) for mode in f.MODES]
    assert outputs[0] == outputs[1] == outputs[2]
    assert grid == original
    outputs[0][0][0] = 9
    assert outputs[1][0][0] == 0 and grid == original


@pytest.mark.parametrize('bad', [None, {}, {'missing_extension': True},
    {'missing_extension': 1}, {'missing_extension': 'unknown'},
    {'missing_extension': 'bottom', 'extra': 1}])
def test_settings_reject_wrong_keys_types_and_values(bad):
    f = family()
    with pytest.raises(ValueError):
        f.program(bad)


@pytest.mark.parametrize('kind', ['bool', 'float', 'bad_color', 'ragged',
    'small', 'wide', 'edge_header', 'duplicate_header', 'header_gap',
    'interior_dot', 'repeated_match', 'no_matches', 'three_ignored'])
def test_domain_rejects_specific_malformed_or_unsupported_inputs(kind):
    f = family()
    grid = scene()
    if kind == 'bool': grid[3][1] = True
    elif kind == 'float': grid[3][1] = 0.0
    elif kind == 'bad_color': grid[3][1] = 10
    elif kind == 'ragged': grid[-1].pop()
    elif kind == 'small': grid = grid[:7]
    elif kind == 'wide': grid = [row + [0] * 21 for row in grid]
    elif kind == 'edge_header': grid[0][0] = 9
    elif kind == 'duplicate_header': grid[0][4] = 1
    elif kind == 'header_gap': grid[0][4] = 0
    elif kind == 'interior_dot': grid[3][4] = 7
    elif kind == 'repeated_match': grid[3][0] = 2
    elif kind == 'no_matches': grid[1][9] = grid[7][0] = 0
    elif kind == 'three_ignored': grid[2][0] = grid[3][0] = grid[4][0] = 9
    with pytest.raises(ValueError):
        f.apply(grid, {'missing_extension': 'first_hit'})


@pytest.fixture(scope='module')
def protected():
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    execute, identity, bridge = _real_evaluator((ROOT / 'shared/runtime').resolve())
    assert identity['backend'] == 'racket' and identity['protected'] is True
    try:
        yield lambda program, grid: _grid(execute(program, grid))
    finally:
        bridge.close()


def test_protected_literal_labels_and_wrong_intermediate(protected):
    f = family()
    for mode in f.MODES:
        assert protected(f.program({'missing_extension': mode}), scene()) == f.apply(scene(), {'missing_extension': mode})
    assert protected(f.program({'missing_extension': 'first_hit'}), scene()) == EXPECTED_FIRST_HIT
    assert protected(f.first_hit_program(observed='g'), scene()) != EXPECTED_FIRST_HIT


def test_exact_default_executes_all_canonical_pairs(protected):
    f = family()
    program = f.program({'missing_extension': 'bottom'})
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert protected(program, pair['input']) == pair['output']
