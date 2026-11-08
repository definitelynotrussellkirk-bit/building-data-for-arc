"""Behavioral tests for the automatic canonical-memorizer lesson gate."""
from pathlib import Path
import importlib.util
import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'workspace/replay_gate.py'

def module():
    assert SOURCE.is_file(), 'The reusable actual-lesson replay gate is missing'
    spec = importlib.util.spec_from_file_location('replay_gate_tests', SOURCE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def known():
    return [{'input': [[1, 1]], 'output': [[2, 2]]},
            {'input': [[3, 3]], 'output': [[4, 4]]}]


def test_known_demonstrations_with_novel_changed_query_are_harmful():
    m = module()
    e = {'train': known(), 'test': [{'input': [[5, 5]], 'output': [[6, 6]]}]}
    r = m.assess_episode(e, m.canonical_map(known()))
    assert r['survives_demos'] and r['wrong_on_query']
    assert r['exact_replay_demonstrations'] == 2
    assert r['unique_demo_inputs'] == 2


def test_one_fresh_changed_demonstration_kills_memorizer():
    m = module()
    e = {'train': known() + [{'input': [[5, 5]], 'output': [[6, 6]]}],
         'test': [{'input': [[7, 7]], 'output': [[8, 8]]}]}
    assert not m.assess_episode(e, m.canonical_map(known()))['survives_demos']


def test_known_query_is_not_reported_as_harmful():
    m = module()
    r = m.assess_episode({'train': known(), 'test': [known()[0]]}, m.canonical_map(known()))
    assert r['survives_demos'] and not r['wrong_on_query']


def test_novel_identity_query_is_not_reported_as_harmful():
    m = module()
    e = {'train': known(), 'test': [{'input': [[5, 5]], 'output': [[5, 5]]}]}
    assert not m.assess_episode(e, m.canonical_map(known()))['wrong_on_query']


def test_duplicate_demo_inputs_are_counted_honestly():
    m = module()
    e = {'train': [known()[0]] * 3, 'test': [known()[1]]}
    r = m.assess_episode(e, m.canonical_map(known()))
    assert r['unique_demo_inputs'] == 1
    assert r['exact_replay_demonstrations'] == 3


def test_conflicting_canonical_labels_fail_closed():
    m = module()
    with pytest.raises(ValueError, match='conflicting'):
        m.canonical_map([known()[0], {'input': [[1, 1]], 'output': [[9, 9]]}])


def test_empty_demonstrations_do_not_vacuously_pass():
    m = module()
    with pytest.raises(ValueError, match='demonstration'):
        m.assess_episode({'train': [], 'test': known()}, m.canonical_map(known()))
