"""Prototype-scoped behavior, Racket, teaching, and public export regressions."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/prototype.py'


def test_prototype_entry_exists():
    assert SOURCE.is_file(), 'The runnable parameter prototype has not been implemented'


@pytest.fixture(scope='module')
def proto():
    assert SOURCE.is_file(), 'The runnable parameter prototype has not been implemented'
    spec = importlib.util.spec_from_file_location('bridge_parametric_test_subject', SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def reference(proto):
    with proto.RacketReference() as ref:
        yield ref


def fixed_grid():
    grid = [[0] * 9 for _ in range(7)]
    grid[2][1] = grid[3][1] = 8
    grid[2][7] = grid[3][7] = 2
    return grid


@pytest.mark.parametrize('center,expected', [('preserve', 0), ('near', 8), ('far', 2)])
@pytest.mark.parametrize('transpose', [False, True])
def test_odd_middle_ownership_is_geometric_and_racket_executed(proto, reference, center, expected, transpose):
    grid = fixed_grid()
    if transpose:
        grid = [list(row) for row in zip(*grid)]
    original = copy.deepcopy(grid)
    result = reference.apply(proto.materialize_program(center), grid)
    if transpose:
        assert result[4] == [expected] * 7
        assert result[2] == result[3] == [8] * 7
        assert result[5] == result[6] == [2] * 7
    else:
        assert all(row[4] == expected for row in result)
        assert all(row[2:4] == [8, 8] and row[5:7] == [2, 2] for row in result)
    assert result == proto.transform(grid, center)
    assert grid == original


def test_default_program_is_the_exact_canonical_program(proto, reference):
    assert proto.materialize_program('preserve') == proto.canonical_program()
    assert proto.canonical_rule_hash() == 'adc52fde010d'
    pairs = proto.canonical_examples()
    assert len(pairs) == 5
    for pair in pairs:
        assert reference.apply(proto.materialize_program('preserve'), pair['input']) == pair['output']


@pytest.mark.parametrize('center', ['preserve', 'near', 'far'])
def test_episode_counts_uniqueness_racket_labels_and_demo_only_identifiability(proto, reference, center):
    episode = proto.generate_episode(17, center=center, n_train=4, n_test=4, reference=reference)
    assert len(episode['train']) == len(episode['test']) == 4
    pairs = episode['train'] + episode['test']
    assert len({json.dumps(p['input']) for p in pairs}) == 8
    assert episode['private']['parameters'] == {'center': center}
    for pair in pairs:
        assert reference.apply(episode['private']['program'], pair['input']) == pair['output']
    assert episode['private']['teaching']['consistent_settings'] == [center]
    assert all(row['identifiable'] for row in episode['private']['teaching']['queries'])
    assert len(episode['private']['teaching']['queries']) == 4
    assert any(len(p['input']) == len(p['input'][0]) == 30 for p in episode['test'])
    for key in ('horizontal_only', 'vertical_only', 'vertical_first', 'bounded_span', 'lower_color_near', 'identity'):
        assert not episode['private']['teaching']['shortcut_rivals'][key]['fits_demonstrations']


def test_independent_count_controls_exact_dimensions_and_rng_independence(proto, reference):
    random.seed(327); state = random.getstate()
    a = proto.generate_episode(73, center='far', n_train=2, n_test=5, height=30, width=27, reference=reference)
    b = proto.generate_episode(73, center='far', n_train=2, n_test=5, height=30, width=27, reference=reference)
    assert a == b and random.getstate() == state
    assert len(a['train']) == 2 and len(a['test']) == 5
    assert all((len(p['input']), len(p['input'][0])) == (30, 27) for p in a['train'] + a['test'])
    assert all(p['identifiable'] for p in a['private']['teaching']['queries'])


@pytest.mark.parametrize('kwargs', [
    {'center': 'left'}, {'n_train': 1}, {'n_train': True}, {'n_test': 0},
    {'n_test': 33}, {'height': 6}, {'width': 31}, {'height': True},
])
def test_invalid_controls_fail_before_reference_execution(proto, kwargs):
    with pytest.raises(ValueError):
        proto.generate_episode(1, **kwargs)


def test_query_answers_and_private_metadata_do_not_influence_public_bytes_or_name(proto, reference, tmp_path):
    episode = proto.generate_episode(109, center='near', reference=reference)
    changed = copy.deepcopy(episode)
    changed['private'] = {'seed': -999, 'parameters': {'center': 'far'}, 'program': 'not a rule'}
    for pair in changed['test']:
        pair['output'] = [[9]]
    original = proto.public_challenge_bytes(episode)
    assert proto.public_challenge_bytes(changed) == original
    assert proto.public_challenge_id(changed) == hashlib.sha256(original).hexdigest()
    one = proto.write_batch([episode], tmp_path/'one')
    two = proto.write_batch([changed], tmp_path/'two')
    assert sorted(p.name for p in (tmp_path/'one/public').iterdir()) == sorted(p.name for p in (tmp_path/'two/public').iterdir())
    public_file = next((tmp_path/'one/public').iterdir())
    assert public_file.read_bytes() == original
    assert public_file.stem == hashlib.sha256(original).hexdigest()
    public = json.loads(original)
    assert set(public) == {'train', 'test'}
    assert all(set(p) == {'input'} for p in public['test'])
    with pytest.raises(ValueError, match='duplicate'):
        proto.write_batch([episode, changed], tmp_path/'duplicates')
    assert not (tmp_path/'duplicates').exists()


def test_batch_order_is_public_content_order_and_rejects_existing_destination(proto, reference, tmp_path):
    episodes = [proto.generate_episode(201, center=center, reference=reference) for center in proto.CENTER_VALUES]
    result = proto.write_batch(list(reversed(episodes)), tmp_path/'batch')
    assert [row['public_id'] for row in result['episodes']] == sorted(proto.public_challenge_id(e) for e in episodes)
    assert all(row['public_id'] == hashlib.sha256((tmp_path/'batch/public'/f"{row['public_id']}.json").read_bytes()).hexdigest() for row in result['episodes'])
    with pytest.raises(FileExistsError):
        proto.write_batch(episodes, tmp_path/'batch')


def even_grid():
    grid = [[0] * 10 for _ in range(7)]
    grid[2][1] = grid[3][1] = 8
    grid[2][8] = grid[3][8] = 2
    return grid


def test_even_gaps_are_unchanged_by_center_policy(proto, reference):
    for grid in (even_grid(), [list(row) for row in zip(*even_grid())]):
        outputs = [reference.apply(proto.materialize_program(center), grid) for center in proto.CENTER_VALUES]
        assert outputs[0] == outputs[1] == outputs[2]


def test_even_only_demonstrations_do_not_identify_an_odd_gap_query(proto, reference):
    inputs = [even_grid(), [list(row) for row in zip(*even_grid())]]
    train = [{'input': g, 'output': reference.apply(proto.materialize_program('near'), g)} for g in inputs]
    assessment = proto.assess_teaching(train, [fixed_grid()], 'near', reference)
    assert assessment['consistent_settings'] == list(proto.CENTER_VALUES)
    assert not assessment['queries'][0]['identifiable']
    assert assessment['queries'][0]['distinct_surviving_predictions'] == 3


def test_setting_changes_transformation_not_sampled_inputs(proto, reference):
    episodes = [proto.generate_episode(17, center=center, reference=reference) for center in proto.CENTER_VALUES]
    inputs = [[p['input'] for p in e['train'] + e['test']] for e in episodes]
    assert inputs[0] == inputs[1] == inputs[2]
    for i in range(8):
        facts, errors = proto.GENERATOR._branch_facts(inputs[0][i])
        assert not errors
        answers = [json.dumps((e['train'] + e['test'])[i]['output']) for e in episodes]
        assert len(set(answers)) == (3 if facts['gap'] % 2 else 1)
