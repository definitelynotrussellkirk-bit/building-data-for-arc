"""Episode-level contracts: a fixed taught setting and independent counts."""
import importlib.util
import json
import random

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / 'generators/48bda9528e71/workspace/parametric'
MODES = ('one_step', 'to_boundary')


def adapter():
    path = HOME / 'adapter.py'
    assert path.is_file(), 'native adapter not implemented yet'
    spec = importlib.util.spec_from_file_location('projection_adapter_test', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('seed', [0, 17])
def test_setting_independent_inputs_and_demo_only_discrimination(seed):
    a = adapter()
    episodes = [a.generate(seed, {'projection_reach': mode}, 3, 4) for mode in MODES]
    for episode, mode in zip(episodes, MODES):
        assert set(episode) == {'train', 'test', 'program_solution'}
        assert episode['program_solution'] == a.program({'projection_reach': mode})
        assert len(episode['train']) == 3 and len(episode['test']) == 4
        keys = [json.dumps(p['input']) for split in ('train', 'test') for p in episode[split]]
        assert len(set(keys)) == 7
    for i in range(len(MODES)):
        for j in range(i):
            for split in ('train', 'test'):
                assert [p['input'] for p in episodes[i][split]] == [p['input'] for p in episodes[j][split]]
            assert any(x['output'] != y['output'] for x, y in zip(episodes[i]['train'], episodes[j]['train']))


@pytest.mark.parametrize('seed', [0, 1, 2])
def test_default_is_episode_fixed_and_seed_deterministic(seed):
    a = adapter(); state = random.getstate()
    actual = a.generate(seed)
    assert actual == a.generate(seed, {'projection_reach': MODES[seed % len(MODES)]})
    assert random.getstate() == state


def test_independent_count_prefixes_and_freshness():
    a = adapter(); setting = {'projection_reach': 'to_boundary'}
    full = a.generate(2**63 - 1, setting, 6, 4)
    for demos, queries in ((3, 1), (3, 4), (4, 2), (5, 3), (6, 1)):
        small = a.generate(2**63 - 1, setting, demos, queries)
        assert small['train'] == full['train'][:demos]
        assert small['test'] == full['test'][:queries]
    full['train'][0]['input'][0][0] = 99
    full['test'][0]['output'][0][0] = 99
    assert all(v != 99 for split in ('train', 'test') for p in a.generate(2**63 - 1, setting, 6, 4)[split]
               for name in ('input', 'output') for row in p[name] for v in row)


@pytest.mark.parametrize('settings', [[], {}, {'projection_reach': 0}, {'projection_reach': True},
    {'projection_reach': 'bad'}, {'projection_reach': 'one_step', 'other': 1}])
def test_reject_malformed_settings(settings):
    with pytest.raises(ValueError): adapter().generate(0, settings)


@pytest.mark.parametrize('kwargs', [
    {'seed': True}, {'seed': 0.5}, {'seed': -1}, {'seed': 2**63},
    {'seed': 0, 'demos': 2}, {'seed': 0, 'demos': 7}, {'seed': 0, 'demos': True},
    {'seed': 0, 'queries': 0}, {'seed': 0, 'queries': 5}, {'seed': 0, 'queries': 1.0}])
def test_reject_invalid_native_request(kwargs):
    with pytest.raises(ValueError): adapter().generate(**kwargs)
