"""Behavioral checks for the separate orbit/link native prototype."""
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def family():
    path = HOME / 'workspace/parametric/native_family.py'
    assert path.is_file(), 'native orbit/link family has not been implemented'
    spec = importlib.util.spec_from_file_location('orbit_family_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene():
    grid = [[0] * 9 for _ in range(9)]
    for r, c in ((0, 0), (0, 1), (1, 1)):
        grid[r][c] = 6
    grid[4][4] = 9
    return grid


def wanted(links):
    grid = [[0] * 9 for _ in range(9)]
    for r, c in ((1, 3), (1, 4), (2, 4), (3, 7), (4, 6), (4, 7),
                 (6, 3), (7, 3), (7, 4), (3, 1), (3, 2), (4, 1)):
        grid[r][c] = 6
    grid[4][4] = 9
    if links:
        for r, c in ((3, 4), (4, 5), (5, 4), (6, 4), (4, 3), (4, 2)):
            grid[r][c] = 9
    return grid


@pytest.mark.parametrize('links', ['none', 'first_hit'])
def test_even_width_rotation_and_first_hit_have_literal_outputs(links):
    f = family()
    grid = scene()
    assert f.apply(grid, {'links': links}) == wanted(links == 'first_hit')
    assert grid == scene(), 'the caller input must remain unmodified'


def test_default_is_exact_selected_canonical_program():
    from arcpuzzles import Catalog
    f = family()
    row = Catalog(HOME.parents[1]).get('7fe59337a0b4')
    canonical = {v['program_solution'] for v in row['variants']}
    assert canonical == {f.program({'links': 'none'})}


@pytest.mark.parametrize('settings', [None, {}, {'links': True}, {'links': 0},
    {'links': 'first-hit'}, {'links': 'none', 'seed': 1}, []])
def test_settings_reject_undeclared_types_and_keys(settings):
    with pytest.raises(ValueError):
        family().program(settings)


@pytest.mark.parametrize('mutation', ['bool', 'float', 'ragged', 'two_markers',
    'no_marker', 'mixed_colors', 'disconnected', 'clipped', 'symmetric'])
def test_admitted_grammar_rejects_ambiguous_or_invalid_inputs(mutation):
    grid = scene()
    if mutation == 'bool': grid[0][0] = True
    elif mutation == 'float': grid[0][0] = 6.0
    elif mutation == 'ragged': grid[0].pop()
    elif mutation == 'two_markers': grid[8][8] = 9
    elif mutation == 'no_marker': grid[4][4] = 0
    elif mutation == 'mixed_colors': grid[0][0] = 2
    elif mutation == 'disconnected': grid[8][8] = 6
    elif mutation == 'clipped': grid[4][4] = 0; grid[1][4] = 9
    elif mutation == 'symmetric': grid[1][0] = 6
    with pytest.raises(ValueError):
        family().apply(grid, {'links': 'none'})


@pytest.mark.parametrize('links', ['none', 'first_hit'])
def test_protected_racket_matches_hand_checked_even_width_fixture(links):
    from arcpuzzles.parametric_worker import _real_evaluator
    f = family()
    apply, identity, bridge = _real_evaluator(HOME.parents[1] / 'shared/runtime')
    try:
        assert identity['backend'] == 'racket' and identity['protected'] is True
        assert apply(f.program({'links': links}), scene()) == wanted(links == 'first_hit')
    finally:
        bridge.close()


def test_private_ray_rivals_have_the_stated_meaning_in_racket():
    from arcpuzzles.parametric_worker import _real_evaluator
    f = family()
    execute, _, bridge = _real_evaluator(HOME.parents[1] / 'shared/runtime')
    try:
        assert execute(f.linked_program(occupancy='g'), scene()) == wanted(False)
        for mode, marker_cells, motif_cells in [
            ('one_cell', 5, 12), ('two_cells', 7, 12), ('to_edge', 11, 12),
            ('overwrite_hit', 11, 8), ('north_length', 5, 12)]:
            actual = execute(f.linked_program(mode=mode), scene())
            assert sum(v == 9 for row in actual for v in row) == marker_cells
            assert sum(v == 6 for row in actual for v in row) == motif_cells
    finally:
        bridge.close()


def test_first_blocker_preserves_zeros_behind_it():
    from arcpuzzles.parametric_worker import _real_evaluator
    f = family()
    grid = [[0] * 15 for _ in range(15)]
    for r, c in [(r, 0) for r in range(5)] + [(0, 1), (0, 2), (2, 1)]:
        grid[r][c] = 3
    grid[7][7] = 9
    execute, _, bridge = _real_evaluator(HOME.parents[1] / 'shared/runtime')
    try:
        correct = execute(f.program({'links': 'first_hit'}), grid)
        wrong = execute(f.linked_program(mode='last_hit'), grid)
        assert correct[4][7] == 9 and correct[3][7] == 3
        assert correct[2][7] == 0 and wrong[2][7] == 9
        assert sum(v == 9 for row in correct for v in row) == 13
        assert sum(v == 9 for row in wrong for v in row) == 17
    finally:
        bridge.close()
