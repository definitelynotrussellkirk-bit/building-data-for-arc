"""Contract and distinguishing-example checks for the gravity composition."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

ROOT = find_root(__file__)
HOME = ROOT / 'generators/49fe4f572f8d/workspace/parametric'


def load():
    path = HOME / 'adapter.py'
    assert path.is_file(), 'Native parametric adapter is not implemented'
    spec = importlib.util.spec_from_file_location('_test_gravity_adapter', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_default_is_exact_authority():
    adapter = load()
    rules = {v['program_solution'] for line in canonical_path(ROOT).open()
             if (v := json.loads(line)).get('task_id') == '49fe4f572f8d'}
    assert rules == {adapter.program({'mode': 'down'})}
    assert adapter.program({'mode': 'settle_clear_once'}) not in rules


@pytest.mark.parametrize('demos,queries', [(2, 1), (2, 4), (3, 4), (6, 8)])
def test_counts_distinct_inputs_and_paired_settings(demos, queries):
    adapter = load()
    episodes = [adapter.generate(17, {'mode': mode}, demos, queries)
                for mode in ('down', 'settle_clear_once')]
    for episode in episodes:
        assert len(episode['train']) == demos
        assert len(episode['test']) == queries
        inputs = [p['input'] for p in episode['train'] + episode['test']]
        assert len({json.dumps(g) for g in inputs}) == demos + queries
        assert all(type(v) is int and 0 <= v <= 9 for g in inputs for row in g for v in row)
    assert [p['input'] for p in episodes[0]['train'] + episodes[0]['test']] == [
        p['input'] for p in episodes[1]['train'] + episodes[1]['test']]
    assert episodes[0]['train'] != episodes[1]['train']


def test_counts_do_not_change_shared_examples_or_first_turn():
    adapter = load()
    small = adapter.generate(0, {'mode': 'settle_clear_once'}, 2, 1)
    large = adapter.generate(0, {'mode': 'settle_clear_once'}, 6, 8)
    assert small['train'] == large['train'][:2]
    assert small['test'] == large['test'][:1]
    four = adapter.generate(0, {'mode': 'settle_clear_once'}, 2, 4)
    assert adapter.prototype.turn_bytes(small, 0) == adapter.prototype.turn_bytes(four, 0)
    turn = json.loads(adapter.prototype.turn_bytes(four, 0))
    assert set(turn) == {'train', 'test'}
    assert len(turn['test']) == 1
    assert set(turn['test'][0]) == {'input'}


def test_rectangular_boundaries_and_meaningful_dense_canvas():
    episode = load().generate(0, {'mode': 'down'}, 2, 4)
    grids = [p['input'] for p in episode['test']]
    assert [(len(g), len(g[0])) for g in grids] == [(6, 7), (30, 30), (6, 30), (30, 7)]
    grid = grids[1]
    assert sum(v != 0 for row in grid for v in row) >= 300
    assert all(any(row[c] for row in grid) for c in range(30))
    assert any(grid[0]) and any(grid[-1])


@pytest.mark.parametrize('mode', ['down', 'settle_clear_once'])
def test_two_demos_refute_every_declared_rival(mode):
    adapter = load()
    episode = adapter.generate(13, {'mode': mode}, 2, 4)
    report = adapter.prototype.teaching_check(episode, mode)
    assert report['setting_survivors'] == [mode]
    assert report['demo_survivors'] == []
    assert report['query_changing_survivors'] == []


def test_one_pass_keeps_the_group_created_by_final_gravity():
    module = load().prototype
    grid = [[0] * 7 for _ in range(6)]
    for r, c, value in [(0, 1, 2), (0, 2, 2), (1, 1, 1), (1, 4, 1),
                        (2, 2, 2), (3, 1, 1), (4, 1, 1)]:
        grid[r][c] = value
    expected = [[0] * 7 for _ in range(6)]
    for r, c, value in [(4, 2, 2), (5, 1, 2), (5, 2, 2), (5, 4, 1)]:
        expected[r][c] = value
    assert module.predict(grid, 'settle_clear_once') == expected
    rivals = module.rival_predictions(grid, 'settle_clear_once')
    for name in ('clear_before_gravity', 'omit_final_gravity', 'repeat_until_stable',
                 'threshold_two', 'threshold_four', 'clear_whole_colors'):
        assert rivals[name] != expected, name


@pytest.mark.parametrize('seed,demos,queries', [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
                         (0, True, 4), (0, 1, 4), (0, 7, 4),
                         (0, 3, False), (0, 3, 0), (0, 3, 9)])
def test_invalid_counts_and_seed_rejected(seed, demos, queries):
    with pytest.raises(ValueError):
        load().generate(seed, {'mode': 'down'}, demos, queries)


@pytest.mark.parametrize('settings', [{}, {'mode': True}, {'mode': 'random'},
                                     {'mode': 'down', 'extra': 1}])
def test_bad_settings_rejected(settings):
    with pytest.raises(ValueError):
        load().program(settings)


def test_private_changes_do_not_change_public_projection():
    adapter = load()
    episode = adapter.generate(17, {'mode': 'down'}, 2, 4)
    changed = deepcopy(episode)
    changed.update(settings={'mode': 'secret'}, seed=999, program_solution='secret')
    changed['test'][0]['output'] = [[True]]
    assert public_challenge_bytes(episode) == public_challenge_bytes(changed)
    assert hashlib.sha256(public_challenge_bytes(episode)).hexdigest() == adapter.prototype.public_id(episode)


def test_visible_bool_grid_is_rejected():
    episode = load().generate(17, {'mode': 'down'}, 2, 4)
    episode['train'][0]['input'][0][0] = True
    with pytest.raises(ValueError):
        public_challenge_bytes(episode)
