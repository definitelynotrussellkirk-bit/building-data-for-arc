"""Behavioral tests for the opt-in plus-census family, not production approval."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import random
import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]

def load_adapter():
    path = HOME / 'workspace/parametric/adapter.py'
    assert path.is_file(), 'the native parametric adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('plus_census_adapter_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def fixture():
    grid = [[6] * 15 for _ in range(15)]
    for row, col, color in [(2,2,2), (6,2,2), (10,2,2), (2,10,3), (6,10,3)]:
        grid[row][col] = 4
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            grid[row+dr][col+dc] = color
    grid[10][10] = 4
    grid[9][10] = grid[11][10] = grid[10][9] = 2
    grid[10][11] = 3
    grid[6][6] = 5
    grid[5][6] = grid[7][6] = grid[6][5] = grid[6][7] = 2
    grid[14][14] = 2
    return grid

def test_default_preserves_selected_canonical_source_exactly():
    adapter = load_adapter()
    with canonical_path(find_root(__file__)).open() as handle:
        programs = {row['program_solution'] for line in handle
                    if (row := json.loads(line)).get('task_id') == 'b57f299dcdb3'}
    assert programs == {adapter.program({'readout': 'winner_color'})}

def test_mask_keeps_whole_winning_pluses_and_rejects_loose_pixels():
    adapter = load_adapter()
    grid = fixture()
    before = copy.deepcopy(grid)
    assert adapter.solve_python(grid, {'readout': 'winner_color'}) == [[2]]
    expected = [[0] * 15 for _ in range(15)]
    for row in (2, 6, 10):
        expected[row][2] = 4
        expected[row-1][2] = expected[row+1][2] = 2
        expected[row][1] = expected[row][3] = 2
    assert adapter.solve_python(grid, {'readout': 'winner_pluses'}) == expected
    assert grid == before

def test_census_change_selects_different_untouched_objects():
    adapter = load_adapter()
    before = fixture()
    after = copy.deepcopy(before)
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        after[10+dr][2+dc] = 3
    assert adapter.solve_python(after, {'readout': 'winner_color'}) == [[3]]
    old = adapter.solve_python(before, {'readout': 'winner_pluses'})
    new = adapter.solve_python(after, {'readout': 'winner_pluses'})
    assert before[2][2] == after[2][2] == 4
    assert old[2][2] == 4 and new[2][2] == 0
    assert old[2][10] == 0 and new[2][10] == 4

@pytest.mark.parametrize('demos', [2, 3, 6])
@pytest.mark.parametrize('seed', [0, 17])
def test_independent_counts_distinct_inputs_and_large_content(seed, demos):
    adapter = load_adapter()
    state = random.getstate()
    color = adapter.generate(seed, {'readout': 'winner_color'}, demos, 4)
    mask = adapter.generate(seed, {'readout': 'winner_pluses'}, demos, 4)
    assert len(mask['train']) == demos and len(mask['test']) == 4
    for split in ('train', 'test'):
        assert [p['input'] for p in color[split]] == [p['input'] for p in mask[split]]
    inputs = [json.dumps(pair['input']) for pair in mask['train'] + mask['test']]
    assert len(set(inputs)) == demos + 4
    large = mask['test'][-1]
    assert len(large['input']) == len(large['input'][0]) == 30
    assert len(large['output']) == len(large['output'][0]) == 30
    occupied = [(r,c) for r,row in enumerate(large['output']) for c,x in enumerate(row) if x]
    assert max(r for r,_ in occupied) - min(r for r,_ in occupied) >= 24
    assert max(c for _,c in occupied) - min(c for _,c in occupied) >= 24
    assert random.getstate() == state
    assert adapter.generate(seed, {'readout': 'winner_pluses'}, demos, 4) == mask

def test_first_turn_does_not_depend_on_number_of_future_queries():
    adapter = load_adapter()
    one = adapter.generate(8, {'readout': 'winner_pluses'}, 3, 1)
    four = adapter.generate(8, {'readout': 'winner_pluses'}, 3, 4)
    assert one['train'] == four['train']
    assert one['test'][0] == four['test'][0]
    first = {'train': four['train'], 'test': four['test'][:1]}
    assert public_challenge_bytes(one) == public_challenge_bytes(first)
    changed = copy.deepcopy(first)
    changed.update(settings={'readout': 'private'}, seed=999, program_solution='private')
    changed['test'][0]['output'] = [[9]]
    assert public_challenge_id(first) == public_challenge_id(changed)
    public = json.loads(public_challenge_bytes(first))
    assert set(public) == {'train', 'test'}
    assert set(public['test'][0]) == {'input'}

@pytest.mark.parametrize('seed,demos,queries', [
    (True,3,4), (-1,3,4), (2**63,3,4), (0,1,4), (0,7,4),
    (0,True,4), (0,3,0), (0,3,5), (0,3,4.0),
])
def test_invalid_requests_fail_closed(seed, demos, queries):
    with pytest.raises(ValueError):
        load_adapter().generate(seed, {'readout': 'winner_color'}, demos, queries)

@pytest.mark.parametrize('settings', [{}, {'readout':True}, {'readout':'other'},
                                        {'readout':'winner_color','extra':1}])
def test_unknown_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        load_adapter().program(settings)

def test_programs_execute_through_protected_racket():
    from arcpuzzles.parametric_worker import _real_evaluator
    adapter = load_adapter()
    root = find_root(__file__)
    apply, identity, bridge = _real_evaluator(root / 'shared/runtime')
    try:
        assert identity['backend'] == 'racket' and identity['protected'] is True
        for readout in ('winner_color', 'winner_pluses'):
            settings = {'readout': readout}
            grid = fixture()
            assert apply(adapter.program(settings), grid) == adapter.solve_python(grid, settings)
    finally:
        bridge.close()
