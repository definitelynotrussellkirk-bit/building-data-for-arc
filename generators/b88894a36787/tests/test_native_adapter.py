"""Native request isolation, settings observability and strict public API."""
import importlib.util
import json
import random

import pytest
from reviewer_support import find_root

HOME = find_root(__file__) / 'generators/b88894a36787/workspace/parametric'


def adapter():
    path = HOME / 'adapter.py'
    assert path.is_file(), 'native adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('native_route_adapter_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(episode, split):
    return [pair['input'] for pair in episode[split]]


def test_three_settings_share_inputs_and_are_taught_by_the_minimum_lesson():
    a = adapter()
    modes = ('bottom', 'penultimate', 'first_hit')
    for seed in (0, 17, 2**63 - 1):
        episodes = [a.generate(seed, {'missing_extension': mode}) for mode in modes]
        for episode in episodes:
            assert (len(episode['train']), len(episode['test'])) == (3, 4)
            assert inputs(episode, 'train') == inputs(episodes[0], 'train')
            assert inputs(episode, 'test') == inputs(episodes[0], 'test')
            assert len({json.dumps(p['input']) for p in episode['train'] + episode['test']}) == 7
        for i in range(3):
            assert episodes[i]['program_solution'] == a.program({'missing_extension': modes[i]})
            for j in range(i):
                assert any(p['output'] != q['output'] for p, q in zip(episodes[i]['train'], episodes[j]['train']))


def test_implicit_setting_is_deterministic_and_queries_do_not_depend_on_demo_count():
    a = adapter()
    for seed in (0, 1, 2, 17):
        chosen = {'missing_extension': ('bottom', 'penultimate', 'first_hit')[seed % 3]}
        small = a.generate(seed, demos=3, queries=1)
        full = a.generate(seed, chosen, demos=6, queries=4)
        assert small['program_solution'] == a.program(chosen)
        assert small['train'] == full['train'][:3]
        assert small['test'] == full['test'][:1]


def test_requests_are_fresh_and_do_not_change_global_rng():
    a = adapter()
    before = random.getstate()
    original = a.generate(17)
    other = a.generate(17)
    assert before == random.getstate() and original == other
    other['train'][0]['input'][0][0] = 9
    other['test'][0]['output'][0][0] = 9
    assert original == a.generate(17)


@pytest.mark.parametrize('seed', [True, 1.0, '1', None, -1, 2**63])
def test_invalid_seed_is_rejected(seed):
    a = adapter()
    with pytest.raises((TypeError, ValueError)):
        a.generate(seed)


@pytest.mark.parametrize('settings', [{}, {'missing_extension': True},
    {'missing_extension': 'bad'}, {'missing_extension': 'bottom', 'extra': 1}])
def test_invalid_explicit_settings_are_rejected(settings):
    a = adapter()
    with pytest.raises(ValueError):
        a.generate(0, settings)


@pytest.mark.parametrize('kwargs', [{'demos': 2}, {'demos': 7}, {'demos': True},
    {'queries': 0}, {'queries': 5}, {'queries': 4.0}, {'extra': 1}])
def test_unsupported_requests_are_rejected(kwargs):
    a = adapter()
    with pytest.raises((TypeError, ValueError)):
        a.generate(0, **kwargs)
