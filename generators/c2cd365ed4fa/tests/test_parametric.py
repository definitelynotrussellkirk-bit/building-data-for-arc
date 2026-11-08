"""Contract/regression tests for the separate histogram parametric adapter."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

ROOT = find_root(__file__)
HOME = ROOT / 'generators/c2cd365ed4fa/workspace/parametric'


def load():
    path = HOME / 'adapter.py'
    assert path.is_file(), 'Native parametric adapter is not implemented'
    spec = importlib.util.spec_from_file_location('_test_c2cd_adapter', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_default_is_exact_authority():
    adapter = load()
    rules = {v['program_solution'] for line in canonical_path(ROOT).open()
             if (v := json.loads(line)).get('task_id') == 'c2cd365ed4fa'}
    assert rules == {adapter.program({'column_order': 'fixed'})}
    assert adapter.program({'column_order': 'count_ascending'}) not in rules


@pytest.mark.parametrize('demos,queries', [(2, 1), (2, 4), (3, 4), (6, 8)])
def test_counts_distinct_inputs_and_paired_settings(demos, queries):
    adapter = load()
    episodes = [adapter.generate(17, {'column_order': mode}, demos, queries)
                for mode in ('fixed', 'count_ascending')]
    for episode in episodes:
        assert len(episode['train']) == demos
        assert len(episode['test']) == queries
        inputs = [p['input'] for p in episode['train'] + episode['test']]
        assert len({json.dumps(g) for g in inputs}) == demos + queries
        assert all(type(v) is int and 0 <= v <= 9
                   for g in inputs for row in g for v in row)
    assert [p['input'] for p in episodes[0]['train'] + episodes[0]['test']] == [
        p['input'] for p in episodes[1]['train'] + episodes[1]['test']]
    assert episodes[0]['train'] != episodes[1]['train']


def test_four_queries_preserve_single_query_first_turn():
    adapter = load()
    one = adapter.generate(0, {'column_order': 'count_ascending'}, 3, 1)
    four = adapter.generate(0, {'column_order': 'count_ascending'}, 3, 4)
    assert one['train'] == four['train']
    assert one['test'][0] == four['test'][0]
    assert adapter.prototype.turn_bytes(one, 0) == adapter.prototype.turn_bytes(four, 0)
    turn = json.loads(adapter.prototype.turn_bytes(four, 0))
    assert set(turn) == {'train', 'test'}
    assert len(turn['test']) == 1
    assert set(turn['test'][0]) == {'input'}


def test_minimum_rectangular_and_substantive_maximum_canvas():
    episode = load().generate(0, {'column_order': 'fixed'}, 2, 4)
    grids = [p['input'] for p in episode['test']]
    assert [(len(g), len(g[0])) for g in grids] == [(10, 10), (30, 30), (10, 30), (30, 10)]
    grid = grids[1]
    assert sum(v != 7 for row in grid for v in row) >= 150
    assert all(any(v != 7 for v in edge) for edge in
               [grid[0], grid[-1], [r[0] for r in grid], [r[-1] for r in grid]])


@pytest.mark.parametrize('mode', ['fixed', 'count_ascending'])
def test_two_demos_eliminate_query_changing_declared_shortcuts(mode):
    adapter = load()
    episode = adapter.generate(13, {'column_order': mode}, 2, 4)
    report = adapter.prototype.teaching_check(episode, mode)
    assert report['setting_survivors'] == [mode]
    assert report['query_changing_survivors'] == []
    assert 'four_connected' in report['rivals']
    assert 'pixel_count' in report['rivals']


def test_missing_columns_cannot_be_compacted_and_padded_right():
    adapter = load()
    for mode in ('fixed', 'count_ascending'):
        episode = adapter.generate(17, {'column_order': mode}, 2, 4)
        rivals = adapter.prototype.rival_predictions(episode['train'][1]['input'], mode)
        assert 'compact_pad_right' in rivals
        assert any(adapter.prototype.rival_predictions(p['input'], mode)['compact_pad_right'] != p['output']
                   for p in episode['train'])


@pytest.mark.parametrize('seed,demos,queries', [(True, 3, 4), (-1, 3, 4),
                         (0, True, 4), (0, 1, 4), (0, 7, 4),
                         (0, 3, False), (0, 3, 0), (0, 3, 9)])
def test_invalid_counts_and_seed_rejected(seed, demos, queries):
    with pytest.raises(ValueError):
        load().generate(seed, {'column_order': 'fixed'}, demos, queries)


@pytest.mark.parametrize('settings', [{}, {'column_order': True},
                         {'column_order': 'random'}, {'column_order': 'fixed', 'extra': 1}])
def test_bad_settings_rejected(settings):
    with pytest.raises(ValueError):
        load().program(settings)


def test_private_changes_do_not_change_public_projection():
    adapter = load()
    episode = adapter.generate(17, {'column_order': 'fixed'}, 2, 4)
    changed = deepcopy(episode)
    changed['settings'] = {'column_order': 'secret'}
    changed['seed'] = 999
    changed['program_solution'] = 'secret'
    changed['test'][0]['output'] = [[True]]
    assert public_challenge_bytes(episode) == public_challenge_bytes(changed)
    assert hashlib.sha256(public_challenge_bytes(episode)).hexdigest() == adapter.prototype.public_id(episode)


def test_visible_bool_grid_is_rejected():
    episode = load().generate(17, {'column_order': 'fixed'}, 2, 4)
    episode['train'][0]['input'][0][0] = True
    with pytest.raises(ValueError):
        public_challenge_bytes(episode)
