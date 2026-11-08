"""Prototype-only tests: production generation and its Racket contract stay fixed."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / 'workspace/parametric/prototype.py'


@pytest.fixture(scope='module')
def prototype():
    if not PROTOTYPE.is_file():
        pytest.skip('prototype missing; reported by test_prototype_present')
    spec = importlib.util.spec_from_file_location('parametric_563e1df172df', PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prototype_present():
    assert PROTOTYPE.is_file(), 'task-local turn_order prototype has not been implemented'


def test_default_preserves_exact_canonical_racket(prototype):
    assert prototype.DEFAULT_TURN_ORDER == 'horizontal_first'
    assert prototype.materialize_rule() == prototype.canonical_rule()
    assert prototype.rule_hash(prototype.materialize_rule())[:12] == 'a29452f21143'


def test_canonical_default_parity_all_pairs(prototype):
    pairs = canonical_pairs(prototype.TASK_ID, root=find_root(__file__))
    actual = prototype.execute_rule(prototype.materialize_rule(), [p['input'] for p in pairs])
    assert actual == [p['output'] for p in pairs]
    assert len(pairs) >= 4


def test_lawful_same_input_has_distinct_elbows_and_retained_endpoints(prototype):
    grid = [[0] * 5 for _ in range(4)]
    grid[0][1], grid[3][4] = 2, 3
    before = [row[:] for row in grid]
    horizontal = prototype.execute_rule(prototype.materialize_rule(), [grid])[0]
    vertical = prototype.execute_rule(prototype.materialize_rule('vertical_first'), [grid])[0]
    assert horizontal == [[0, 2, 8, 8, 8], [0, 0, 0, 0, 8], [0, 0, 0, 0, 8], [0, 0, 0, 0, 3]]
    assert vertical == [[0, 2, 0, 0, 0], [0, 8, 0, 0, 0], [0, 8, 0, 0, 0], [0, 8, 8, 8, 3]]
    assert grid == before


@pytest.mark.parametrize('setting', ['horizontal_first', 'vertical_first'])
def test_complete_episode_labels_discriminate_rival(prototype, setting):
    episode = prototype.build_episode(173, turn_order=setting)
    assert len(episode['challenge']['train']) == 4
    assert len(episode['challenge']['test']) == 1
    assert set(episode['challenge']) == {'train', 'test'}
    assert all(set(pair) == {'input', 'output'} for pair in episode['challenge']['train'])
    assert set(episode['challenge']['test'][0]) == {'input'}
    assert len(episode['private']['query_outputs']) == 1
    assert episode['private']['parameters'] == {'turn_order': setting}
    assert episode['private']['rival_setting_check']['rejected_by_demo_indices'] == [0, 1, 2, 3]
    assert episode['private']['rival_setting_check']['query_disagrees'] is True
    inputs = [p['input'] for p in episode['challenge']['train'] + episode['challenge']['test']]
    labels = [p['output'] for p in episode['challenge']['train']] + episode['private']['query_outputs']
    assert labels == prototype.execute_rule(episode['private']['racket_text'], inputs)
    assert episode == prototype.build_episode(173, turn_order=setting)


def test_settings_share_generated_inputs(prototype):
    first = prototype.build_episode(99)
    second = prototype.build_episode(99, turn_order='vertical_first')
    for split in ('train', 'test'):
        assert [p['input'] for p in first['challenge'][split]] == [p['input'] for p in second['challenge'][split]]


def test_seeded_selection_is_fixed_and_replays(prototype):
    selected = {prototype.select_turn_order(seed) for seed in range(20)}
    assert selected == set(prototype.TURN_ORDERS)
    episode = prototype.build_episode(47, turn_order=None)
    assert episode['private']['parameters']['turn_order'] == prototype.select_turn_order(47)
    assert episode == prototype.build_episode(47, turn_order=None)


@pytest.mark.parametrize('bad', ['diagonal', '', 1, True])
def test_invalid_parameter_rejected(prototype, bad):
    with pytest.raises(ValueError, match='turn_order'):
        prototype.materialize_rule(bad)


def test_evidence_refuses_existing_directory(prototype, tmp_path):
    with pytest.raises(FileExistsError):
        prototype.write_evidence(tmp_path, seed=173)
    assert list(tmp_path.iterdir()) == []
